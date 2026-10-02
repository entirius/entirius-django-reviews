# Commands

## Generate Api Key

Command generate api key. You can provide optional argument:
--file_path - that indicates the destination path of the file where it is to be saved

You can see the ApiKeys in grappelli - ApiKey

```bash
manage.py reviews-generate-api-key
```

With django-access installed the command refuses: keys are access tokens there
(`manage.py access_token create --scope reviews.moderate --application <name> --expires-days <days>`).


## Calculate product accepted reviews details

Calculating product accepted reviews details. The command takes all approved reviews and calculates, for each product, the number of reviews and the average value of all approved reviews.
You can see the product accepted reviews details in grappelli - Products reviews details
```bash
manage.py manage_reviews
```

###  Fill ProductRepresentation

Komenda utworzy rekordy w ProductRepresentation na podstawie
sale_channela w PIM’ie manage.py
fill-reviews-product-representation-from-pim <sale_channel_pl>
```bash
manage.py fill-reviews-product-representation-from-pim test_channel_pl
```


### Fill magento_id for products in ProductRepresentation

Command adds magento_id's to products in ProductRepresentation. The file path needs to be specified.

```bash
manage.py fill-products-magento-id <file_path>
```


example:
```csv
sku,id
unit-sku-1, 5481
unit-sku-2, 5482
unit-sku-3, 5483
unit-sku-4, 5484
unit-sku-5, 5513
unit-sku-6
unit-sku-7,
unit-sku-8, 5514
unit-sku-9, 5609
unit-sku-10, 2903
unit-sku-11111, 2953
unit-sku-13, 5305
unit-sku-14, 1111
```
