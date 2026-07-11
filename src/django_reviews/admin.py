# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from django import forms
from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path

from django_reviews.domain.importers.review_importer import ReviewImporter
from django_reviews.enum import ReviewType
from django_reviews.models import APIKey, ProductRepresentation, Rate, Review


class CsvImportForm(forms.Form):
    csv_file = forms.FileField(label="Plik CSV")
    delimiter = forms.CharField(max_length=1, initial=",", required=False, help_text="Delimiter używany w pliku CSV")
    default_status = forms.ChoiceField(
        choices=[(status, status) for status in ReviewType.values],
        initial=ReviewType.ACCEPTED,
        required=False,
        help_text="Domyślny status recenzji, jeśli nie podano w pliku CSV",
    )


@admin.register(APIKey)
class APIKeyReviewAdmin(admin.ModelAdmin):
    model = APIKey
    list_display = ["key"]
    readonly_fields = ["created_at", "modified_at"]


class RateReviewInline(admin.TabularInline):
    model = Rate
    extra = 0


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    inlines = (RateReviewInline,)
    model = Review
    fields = [
        "name",
        "product",
        "customer",
        "status",
        "channel_idx",
        "title",
        "detail",
        "average_rate",
        "source",
        "created_at",
        "modified_at",
        "uuid",
        "is_sent_to_magento",
    ]
    readonly_fields = ["created_at", "modified_at", "uuid", "is_sent_to_magento"]
    list_display = [
        "uuid",
        "customer",
        "status",
        "channel_idx",
        "average_rate",
        "source",
        "product",
        "is_sent_to_magento",
        "created_at",
    ]
    search_fields = ["source", "average_rate", "uuid", "status", "channel_idx", "product__sku"]
    list_filter = ["status", "source", "is_sent_to_magento"]
    ordering = ["-created_at"]

    change_list_template = "admin/review_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("import-csv/", self.import_csv, name="import_reviews_csv"),
        ]
        return custom_urls + urls

    def import_csv(self, request):
        from process_logger import ProcessLogger

        logger = ProcessLogger("IMPORT_REVIEWS_ADMIN", "django_reviews")

        if request.method == "POST":
            form = CsvImportForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = request.FILES["csv_file"]
                delimiter = form.cleaned_data["delimiter"] or ","
                default_status = form.cleaned_data["default_status"] or ReviewType.ACCEPTED

                import os
                import tempfile

                with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
                    temp_path = temp_file.name
                    for chunk in csv_file.chunks():
                        temp_file.write(chunk)

                try:
                    importer = ReviewImporter(
                        filename=temp_path, batch_size=1000, delimiter=delimiter, default_status=default_status
                    )

                    result = importer.import_reviews()

                    messages.success(
                        request,
                        f"Successfully imported {result['reviews_created']} reviews and {result['rates_created']} ratings. "
                        f"Found {result['products_found']} existing products, created {result['products_not_found']} new products. "
                        f"Found and linked {result['customers_found']} customers by email.",
                    )

                except Exception as e:
                    logger.exception(e)
                    msg = repr(e)
                    messages.error(request, f"Error during import. Check logs for details: {msg}")
                finally:
                    os.unlink(temp_path)

                return redirect("..")
        else:
            form = CsvImportForm()

        context = {
            "form": form,
            "title": "Import Reviews from CSV",
            "opts": self.model._meta,
        }
        return render(request, "admin/csv_import_form.html", context)


@admin.register(ProductRepresentation)
class ProductRepresentationAdmin(admin.ModelAdmin):
    model = ProductRepresentation
    fields = ["sku", "average_rate", "number_of_reviews", "name", "magento_id"]
    list_display = ["sku", "average_rate", "number_of_reviews", "name", "magento_id"]
    search_fields = ["sku", "magento_id"]
