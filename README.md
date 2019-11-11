# Hephaestus

## Introduction

A simple image host I wrote to manage the huge number of screenshots, snips and snaps I upload and share with others on a regular basis.  Images are saved to a local sqlite3 database after being uploaded via POST using the application of your choice (ShareX, curl, etc) along with an authorization key to prevent rogue uploads.

I wrote this primarily as an exercise in using Pyramid for the first time, but also because I was tired of hosting large amounts of unmanaged raw images with random filenames.  Perhaps someone else will find this useful, or expand upon it.

## Code Samples

For testing, you can simply leave the defaults in the configuration file (add your own authorization password/hash/string/phrase) and connect to http://localhost:9001

Send a POST request with your key in the authorization header as a form POST request with the id of 'item' (adjustable) to upload an image into the database.  This will return a UUID to request the image at a later date.

example:  http://localhost:9001/upload returns a UUID when the upload is complete, 'cbbafd8d-96a4-4af9-866e-40bb6f5a1436' meaning that the image is now accessible from http://localhost:9001/img/cbbafd8d-96a4-4af9-866e-40bb6f5a1436.

> A bad request, either due to an invalid URL or a bad authorization token always returns 404.  This is intentional.

## Installation

> Virtual Environments are awesome.  Use one.

Clone this repository and run hephaestus.py after adding your own key to config.toml.  You might even feel like binding to a different adapter, changing the port, or changing the database, log file location, or temp directory if you're feeling wild.