# Compost

A load of sh*t from which stuff grows.

An advanced python/jinja2-based static site generator with support for dynamic page generation, pluggable data 
sources, and pluggable render functions.


## Installation

Clone this repo, and run

    pip install -r requirements.txt


## Running Compost

Compost has two modes:

### One time build

Execute the build once:

    compost build config.json
    
This will compile the site to the output directory specified in the config.

### Ongoing builds

If you want Compost to monitor your filesystem for changes and automatically execute the build to keep the site up
to date with changes, you can ask it to do it like this:

    compost integrate config.json
    
This will run until you explicitly terminate it, and run the build every time that a file changes.


## Serving content

Compost does not currently have a built in server, but if you are using python anyway you can use the python server.

Go into your output directory and use:

    python -m SimpleHTTPServer
    
This will serve your site at http://localhost:8000


## Source Files

The source for your site should all be in a single directory (e.g. called `source`), and that directory is structured
as follows:

```
[root]
 + assets
 + content
 |  + pages
 |  \ ... any other custom directories
 + data
 + templates
```

* **assets** - place all your static assets in here: css, js, images, etc.  These will not be processed by compost, they
will just be copied to the output directory on build

* **content** - this is where you place all your actual content files, both pages and fragments of pages, etc.

* **content/pages** - every file in here will map to an output page of the same name.  Compost will use this directory
and any sub-directories as the canonical layout for your site.

* **content/[anything else]** - you are free to define any other directories in here, and reference them when building
your pages.  For example, include a directory called `fragments` and place your templates for re-usable page fragments
in there.

* **data** - place all your data files in this directory (e.g. your csvs, JSON, etc, which contains the data to be plugged
into your site.

* **templates** - place all your general "theme" templates in here.  Your base template, and any other re-usable bits of
layout.



## Configuration

Each run of compost is controlled by a configuration file.  The full default configuration looks like this:

```json
{
    "src_dir" : "source",
    "out_dir" : "serve",
    "build_dir" : "build",

    "plugins" : {
        "data" : {
            "csv" : {
                "shapes" : {
                    "table" : "compost.datasources.csvsources.TableCSVDataSource",
                    "dict" : "compost.datasources.csvsources.DictCSVDataSource"
                },
                "default" : "table"
            }
        }
    }
}
```

* **src_dir** - the directory of all your source files

* **out_dir** - the directory where the complied output will be placed

* **build_dir** - a directory where it is safe for compost to place intermediate files during the build.

* **plugins** - configuration for the various kinds of plugins available for the build

* **plugins/data** - configuration for the data plugins.  These are the plugins that make the `data` global variable
available to you in the templates and source files.  See the **Data Plugins** section for more detail.


## Templates

Compost uses Jinja2 as its templating engine, and you should see the Jinja2 documentation for details on how
to use it.

Compost provides a number of global attributes which are available in your templates:

* `data` - this is the entry point to all your data files.  You can access a particular data source by requesting
it from here by name.  For example `data.get("staff")` to retrieve a data file listing your staff.

* `url_for` - this is a utility which can retrieve the correct final URL for a link on your site.


### Working with data

Data files are available to you directly inside the template system via the global `data` keyword.  Each data source
follows the same pattern:

1. Load the data source from the `data` global

2. Spefify the "shape" that you would like the data in (different data sources may support different shapes)

3. Interact with the resulting data (e.g. with an iterator if appropriate)

Consider the following example.  This loads a CSV of staff profiles, converts it to a dictionary, and iterates through
each staff member, outputting a record for them:

```html
<div class="row">
    {% for person in data.get("staff").shape("dict") %}
    <div class="staff col-sm-6 col-lg-3">
        <img src="{{ staff.get("Image") }}"><br>
        <strong>{{ staff.get("Name") }}</strong>
        <p>{{ staff.get("Short Bio") }}</p>
    </div>
    {% endfor %}
</div>
```

Backing this would be a file called `staff.csv` which appears in the `source/data` directory, and which has the columns
"Image", "Name" and "Short Bio".


## Data Plugins

TODO

