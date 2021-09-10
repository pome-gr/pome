<p align="center"><a href="https://pome.gr/">
<img src="https://pome.gr/assets/pome-round.png" width="90px"/>
</a></p>

# What is pome?

`pome` is a distributed accounting software.

## Why pome?

We believe that accounting data is one of the most valuable data of a business.   

Hence, it seems crucial to us that:

1. Entrepreneurs should own their accounting data and not depend on a third-party cloud to access them. 
2. The accounting data should be written using a simple, documented and open human-readable format

This is what pome offers.

Our ambition is to provide the framework for an ecosystem that will let businesses get the most out of their accounting data.

# How does pome work?

`pome` reads and write accounting data locally on your computer in a regular folder that is also a [git repository](https://en.wikipedia.org/wiki/Git). This approach provides a powerful framework to collaboratively work on accounting data in a distributed way.

`pome` provides a web UI that you can access from your browser.

# Getting started

## Install pome

`pome` requires Python 3.9.

We recommend running the below command in a Python 3.9 [virtual environment](https://realpython.com/python-virtual-environments-a-primer/).

```
pip3.9 install pome
```

## Start your company's accounts pome repository

You can use example companies to get started:

```
git clone https://github.com/pome-gr/pome.git
cd pome
cp -r examples/companies/<choose_your_example_company> /path/to/your/new/company/repository
cd /path/to/your/new/company/repository
git init
git add -A
git commit -m "Initial commit"
pome
```

Then open your browser at [http://localholst:5000](http://localholst:5000) to launch the UI.

You can change pome's port by launching pome with the port as first argument: `pome <PORT_NUMBER>`.

## Using a remote git repository

It is common and useful to host your git repository on a server that all your collaborators can access.
Common ways to achieve this are to use services such as [https://github.com](https://github.com) or [https://gitlab.com](https://gitlab.com).

Once you have a remote setup, you can ask pome to pull and push automatically from and to it by setting `"git_communicate_with_remote": true` in `pome_settings.json` at the root of your company's account repository (create the file if it is not present and put in `.gitignore` if you don't want to propagate your settings to your collaborators). 
