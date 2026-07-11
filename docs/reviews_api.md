# Reviews

## GET Products reviews

Zwraca zaakceptowane recenzję dla danego produktu/danych produktów. Zwraca paginowaną odpowiedź.

Parameters:

| Parameter |  Type  |                            Description                             |
|:---------:|:------:|:------------------------------------------------------------------:|
|    sku    | string | zwrócone zostaną tylko recencję dla danych produktów o podanym sku |
|   limit   |  int   |                     maksymalna wielkość strony                     |
|   page    |  int   |                            numer strony                            |


Przykładowa odpowiedź:  

```json
{
    "meta": {
        "status": "OK",
        "message": "",
        "messages": [],
        "regional": {
            "language": null,
            "currency": null,
            "country": null
        }
    },
    "data": [
        {
            "sku": "TANA-BLACK/WHITE-36",
            "title": "To jest mój tytuł",
            "detail": "To jest moja ocena",
            "created_at": "2023-05-24",
            "average_rate": "1.00",
            "ratings": [
                {
                    "rate": 1.0,
                    "rating_name": "rating"
                },
                {
                    "rate": 1.0,
                    "rating_name": "quality"
                },
                {
                    "rate": 1.0,
                    "rating_name": "delivery"
                }
            ]
        },
        {
            "sku": "TANA-BLACK/WHITE-36",
            "title": "To jest mój tytuł",
            "detail": "To jest moja ocena",
            "created_at": "2023-05-24",
            "average_rate": "1.00",
            "ratings": [
                {
                    "rate": 1.0,
                    "rating_name": "rating"
                },
                {
                    "rate": 1.0,
                    "rating_name": "quality"
                },
                {
                    "rate": 1.0,
                    "rating_name": "delivery"
                }
            ]
        }
    ],
    "pagination": {
        "page": 1,
        "limit": 2,
        "pages": 2,
        "records": 4
    }
}
```

Zapytanie z paginacją:  
- `api/reviews/v1/<channel_idx>/reviews/?sku[]=unit-sku-4&limit=1&page=1/`


## POST Product review

`api/reviews/v1/<channel_idx>/reviews/`
Dodaję recenzję do bazy danych oraz wysyła ją do Magento. Recenzji przy tworzeniu nadawany jest uuid oraz status pending.
Wymaga autoryzacji użytkownikiem.

```json
{
    "sku": "TANA-BLACK/WHITE-36",
    "title": "To jest mój tytuł",
    "detail": "To jest moja ocena",
    "source": "magento",
    "ratings":[
        {
        "rate": 1,
        "rating_name": "rating"
        },
        {
        "rate": 1,
        "rating_name": "quality"
        },
      {
      "rate": 1,
      "rating_name": "delivery"
      }
    ]
}
```

Przykładowa odpowiedź:
```json
{
  "meta": {
      "status": "OK",
      "message": "",
      "messages": [],
      "regional": {
          "language": null,
          "currency": null,
          "country": null
        }
    },
  "data": {
      "status": "pending",
      "channel_idx": "test-channel-pl",
      "title": "To jest mój tytuł",
      "detail": "To jest moja ocena",
      "average_rate": 1.0,
      "source": "magento",
      "uuid": "36be1a2b-6abc-480e-a994-29416e77374e",
      "rate": [
          {
            "rate": 1.0,
            "rating_name": "rating"
            },
          {
            "rate": 1.0,
            "rating_name": "quality"
            },
          {
            "rate": 1.0,
            "rating_name": "delivery"
            }
        ]
    }
}
```

## PATCH Product review

`api/reviews/v1/<channel_idx>/<uuid_recenzji>/`
Modyfikuję recenzję o danym uuid. Wymaga podania klucza x-api-key.

Przykładowe body:
```json
{
    "title": "To jest mój tytuł",
    "detail": "To jest moja ocena",
    "source": "magento",
    "status": "pending",
    "ratings":[
        {
        "rate": 5,
        "rating_name": "rating"
        },
        {
        "rate": 5,
        "rating_name": "quality"
        },
        {
        "rate": 5,
        "rating_name": "delivery"
        }
    ]
}
```

Można również modyfikować pojedynczę wartości:
```json
{
    "title": "To jest mój tytuł"
}
```

O tym czy obiekty w kluczu "ratings" będą nadpisane czy dopisane do już obecnych decyduję settings: OVERWRITE_RATES
Jeżeli OVERWRITE_RATES = True to obiekty podczas modyfikowania będą nadpisywane

przykładowy curl:
```
curl --location --request PATCH 'http://127.0.0.1:3300/api/reviews/V1/test-channel-pl/reviews/781f5013-0380-4a5a-b27e-f40eaf0adbc0/' \
--header 'x-api-key: <YOUR_API_KEY>' \
--header 'Content-Type: application/json' \
--data-raw '{
    "title": "To jest mój tytuł",
    "detail": "To jest moja ocena",
    "source": "magento",
    "status": "pending",
    "ratings":[
        {
        "rate": 5,
        "rating_name": "rating"
        },
        {
        "rate": 5,
        "rating_name": "quality"
        },
        {
        "rate": 5,
        "rating_name": "delivery"
        }
    ]
}'
```

Przykładowa odpowiedź zapytania:
```json
{
    "meta": {
        "status": "OK",
        "message": "",
        "messages": [],
        "regional": {
            "language": null,
            "currency": null,
            "country": null
        }
    },
    "data": {
        "status": "pending",
        "channel_idx": "test-channel-pl",
        "title": "To jest mój tytuł",
        "detail": "To jest moja ocena",
        "average_rate": 5.0,
        "source": "magento",
        "uuid": "36be1a2b-6abc-480e-a994-29416e77374e",
        "rate": [
            {
                "rate": 5.0,
                "rating_name": "delivery"
            }
        ]
    }
}
```
`api/reviews/v1/<channel_idx>/reviews/36be1a2b-6abc-480e-a994-29416e77374e/`




