# Django Reviews

## Introduction

This is general documentation for django-reviews package. For api documentation see inside api folder.

## Package description

Django reviews is a django app that serves the functionality of product reviews. Also app serve data as JSON over HTTP/S in a consistent manner.

## Dependencies

### Mandatory

For this django app to work, in any meaningful sense of the word, it requires at least django-utils, magento2-sdk2.

### Settings

Currently, there are several settings that need to be set in order for module to work.The most important setting is:
IS_REVIEW_ENABLED, which tells you whether the review functionality is enabled

See settings.py file inside the module to see details and examples.

Other settings:
- MAX_REVIEW_DETAIL_LENGTH - Maximum review description length
- MAX_REVIEW_TITLE_LENGTH - Maximum review title length
- RATINGS_NAME - Possible review criteria
- AVAILABLE_REVIEW_SOURCE - Possible review sources
- MAX_RATE - Maximum review rate
- OVERWRITE_RATES - If true, when modifying reviews by PATCH, ratings will be overwritten. If false when modifying reviews by PATCH, ratings will be added.

Example:
- MAX_REVIEW_DETAIL_LENGTH = 4000
- MAX_REVIEW_TITLE_LENGTH = 128
- RATINGS_NAME = ["rating","quality","delivery"]
- AVAILABLE_REVIEW_SOURCE = ["self/volkanos", "magento"]
- MAX_RATE = 5
- OVERWRITE_RATE = False