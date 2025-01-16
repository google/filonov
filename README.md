# Filonov - AI Creative Concept Analysis

## Problem statement

When dealing with huge amounts of creatives (video and images) it might be hard
to identify which creative approaches work the best since actual performance is
usually evaluated on a single creative.

## Solution

Filonov allows you to answer the question - what are the similarities between
my media (being image or videos). Simply links to your media, specify tagger
and get results in no time!

## Overview

Project Filonov consists of two major parts:

- Data Pipeline
- Data Visualization

Data Pipeline is currently a set of command-line tools which target is creating a JSON file
with graph of assets (images/video) grouped in clusters based on similarity. Additionally
asset nodes enriched with different metrics from Google Ads API and YouTube API to describe
features and performance metrics of creatives.

Data Visualization is a web application uniformly accessible for all users from http://filonov-ai.web.app.
It's deployed to Firebase Static Hosting and implemented as serverless web application where users
can open data files generated with the Data Pipeline.

## Filonov Data Pipeline

Entry point of the Data Pipeline is a CLI tool called `filonov`
that performs necessary steps to generate input for Filonov UI.
Check [the documentation](libs/filonov/README.md) on how to use `filonov`.

## Filonov Data Visualization

To start using the visualization application we need to prepare graph data
using the Filonov Data Pipeline first. As a result we must get a json file,
which you'll open locally or via a remote link.

The web application is available at: http://filonov-ai.web.app.
It's completely serverless, as such there's no any authorization for accessing it,
it's publicly available.

## Disclaimer

This is not an officially supported Google product. This project is not
eligible for the [Google Open Source Software Vulnerability Rewards
Program](https://bughunters.google.com/open-source-security).
