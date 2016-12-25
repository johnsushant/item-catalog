# Item Catalog

Item catalog is a complete fully functional item cataloging website. It has been developed on the Flask Framework using Python. It makes use of PostgreSQL as its database and Jinja 2 as its templating engine. It lists the latest items from different catagories on its front page and has the following capabilities :-
  - Create, edit and delete items
  - Login using Google Account
  - Provides JSON endpoint for items
  - Change catagories of items

### Installation

Item catalog requires a [Vagrant](https://www.vagrantup.com/downloads.html) and [VirtualBox](https://www.virtualbox.org/wiki/Downloads) to run. It makes use of an Ubuntu Server Box with Flask, PostgreSQL and Python preinstalled on it.
  - Install VirtualBox and Vagrant
  - Download and extract the zipped project.
  - Open command prompt and type the following command :
```sh
    vagrant up
```
  - Use an SSH client like [putty](http://www.chiark.greenend.org.uk/~sgtatham/putty/download.html) to access the virtual machine
 - Change directory to `/vagrant/catalog` and run the following commands to set up the database:
```sh
    psql
    \i catalog-before.sql
    \q
```
- Execute the following command to setup the database using SQL Alchemy ORM :
```sh
    python database_setup.py
```
 - Run the following commands to set insert initial values in the categories table:
```sh
    psql
    \i catalog.sql
    \q
```
- Execute the following command to start the webserver :
```sh
    python project.py
```
  - Go to [localhost:5000](http://localhost:5000/) to access the website.

### Architecture

The python code for the project resides in `project.py`
The templates used by jinja are present in the `/templates` folder.
The static files(css, javascript, images) are present in the `/static` folder.
The database setup code resides in `catalog-before.py` and `catalog.py`