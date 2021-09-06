# What is pome?

We believe that accounting data is one of the most valuable data of a business.   

Hence, it seems evident to us that:

1. Entrepreneurs should own their accounting data and not depend on a cloud/software that owns the data for them   
2. The accounting data should be written using a simple, documented and open human-readable format

This is what pome offers.

Our ambition is to provide a framework for an open source ecosystem that will let businesses get the most out of their accounting data: we invite you to build your own pome's plugins to solve the accounting and business problems that you face.

# How does pome work?

`pome` reads and write accounting data on a [git repository](https://en.wikipedia.org/wiki/Git) which provides a powerful framework to collaboratively work on accounting data in a decentralised way.

`pome`provides a web UI that you can access from your browser.

# Getting started

## Install pome

`pome` latest release is `v0.0.1`.

```
git clone https://github.com/pome-gr/pome.git
cd pome
git checkout tags/v0.0.1 -b v0.0.1-branch
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
ln -s `pwd`/run_pome.py venv/bin/pome
```

## Start your company's account repository

While still having pome's virtual environment activated and being in pome's folder:

```
cp -r examples/companies/<choose_your_example_company> /path/to/your/new/company/repository
cd /path/to/your/new/company/repository
git init
git add -A
git commit -m "Initial commit"
pome
```

Then open your browser at [http://localholst:5000](http://localholst:5000) to launch the UI.

You can change pome's port by launching pome with the port as first argument: `pome <PORT_NUMBER>`.

## Using a git remote

It is common and useful to host your git repository on a server that all your collaborators can access.
Common ways to achieve this are to use services such as [https://github.com](https://github.com) or [https://gitlab.com](https://gitlab.com).

Once you have a remote setup, you can ask pome to pull and push automatically from it by setting `"git_communicate_with_remote": false` in `pome_settings.json` at the root of your company's account repository (create the file if it is not present but put in `.gitignore` if you don't want to propagate your settings to your collaborators). 