# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


from django_reviews.domain.dto.product_representation import ProductRepresentation
from django_reviews.models import ProductRepresentation as ProductRepresentationModel


def fill_reviews_product_representation_from_pim(pim_shop_idx: str):
    try:
        from django_pim.models import ConfigurableLink, Product, RealProduct
    except ImportError:
        raise Exception("fill_reviews_product_representation_from_pim does not have access to django_pim module")

    try:
        products = []
        pim_products: list[Product] = Product.objects.filter(shop__idx=pim_shop_idx)
        for pim_product in pim_products:
            product = ProductRepresentation(sku=pim_product.sku, name=pim_product.name)
            products.append(product)
        ProductRepresentationModel.bulk_update_or_create(products)
    except Exception as e:
        raise e
