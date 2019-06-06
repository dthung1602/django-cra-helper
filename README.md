# django-cra-helper

## Introduction

**django-cra-helper** is the missing link between **Django** and **create-react-app**. By adding this to your Django 
project, you can almost effortlessly inject your React components into your Django templates and initialize component
props via Django context variables.

The ultimate goal of this package is to integrate these two projects with minimal changes to workflows that are 
typically used with either during development. From `npm start` to `python manage.py collectstatic`, your commands 
should work as expected so you can forget about implementation and get back to development!

> Note: For the purposes of this README, the abbreviation **CRA** will be used to refer to **create-react-app**.

## Installation

This package is available for installation via `pip`:

\>>>TODO

```sh
pip install django-cra-helper
```

## Setup & Configuration

Once **django-cra-helper** is installed, `cra_helper` will need to be added to `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'cra_helper',
    'django.contrib.staticfiles',
]
```

> Note: Be careful of apps that require an overloaded or replacement runserver command. `cra_heldper` provides a 
separate runserver command and may conflict with it. An example of such a conflict is with `django.contrib.staticfiles`.
In order to solve such issues, try moving `cra_helper` above those apps or remove the offending app altogether.

Add `cra_helper.template_loader.ReactLoader` to `TEMPLATES['OPTIONS']['loaders']`:

```python
TEMPLATES = [
    {
        # ...
        'DIRS': [os.path.join(BASE_DIR, 'templates')],

        'OPTIONS': {
            # ...             
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
                'cra_helper.template_loader.ReactLoader',
            ],
        },
    },
]
```

> Note: when you use a custom template loader, you have to explicitly specify default ones: 
`django.template.loaders.filesystem.Loader` and `django.template.loaders.app_directories.Loader`

The last necessary settings is the CRA projects:

```python
CRA_APPS = {
    'react_index': {
        'port': 3000,
        'path': '^/$'
    },
    'react_user': {
        'port': 3001,
        'path': '^/user/[0-9]+'
    }
}
```

Here `react_index` and `react_user` are two React project folder, relative to the base directory of 
the Django **project** (the folder containing `manage.py`)

`port` specifies the port of the live server of that React app and `path` is the regular expression represents the path 
that your django backend will serve this React app.    

> Note: `port` and `path` are only required for development server and are ignored when `DEBUG == False`

## Usage

Consider a project with following (simplified) structure:
```text
ProjectRoot
    ├── manage.py
    │
    ├── Project
    │   ├── settings.py
    │   └── urls.py
    │
    ├── django_backend
    │   └── views.py
    │
    ├── templates
    │   └── base.html
    |
    ├── react_index
    │   ├── public
    │   │    ├── index.html
    │   └── src
    │        ├── index.js
    │        └── App.js
    |
    └── react_user
        ├── public
        │    ├── index.html
        └── src
             ├── index.js
             └── App.js 
```

### React app re-architecture

The CRA project will need to undergo a small bit of re-architecture to prepare it to accept input values from Django when
Django serves a view. The following is an example of how a couple of small tweaks to a `react_index/src/index.js` file
will establish a simple API for Django to communicate with the bundled React codebase:

```jsx harmony
import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import './App.css';

function App(props) {
    return (
        <div className="App">
            <header className="App-header">
                <img src={logo} className="App-logo" alt="logo"/>
                <p>
                    Edit <code>src/App.js</code> and save to reload.
                </p>
                <a
                    className="App-link"
                    href="https://reactjs.org"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    HELLO {props.env}
                </a>
            </header>
        </div>
    );
}

/**
 * Maintain a simple map of React components to make it easier
 * for Django to reference individual components
 */
const pages = {
  App,
}

/**
 * If Django hasn't injected these properties into the HTML
 * template that's loading this script then we're viewing it
 * via the create-react-app liveserver
 */
window.component = window.component || 'App';
window.props = window.props || { env: 'create-react-app' };
window.reactRoot = window.reactRoot || document.getElementById('root');

/**
 * React the component as usual
 */
ReactDOM.render(
  React.createElement(pages[window.component], window.props),
  window.reactRoot,
);
```

Basically, `index.js` is updated to read values set to `window.component`, `window.props`, and `window.reactRoot` and 
use these to render a component. Each of these three "inputs" will allow Django to easily specify which component to 
initialize on a per-view basis:

* `window.component`: A **string** that points to a Component entry in `pages`
* `window.props`: An **Object** containing props to get passed into the Component
* `window.reactRoot`: an **instance** of `document.getElementById`

> Note: Settings these values is optional. The defaults specified in the template above enable components to render as 
expected when viewed from the CRA liveserver.

Below is `react_user/public/index.html` that will render the context:

```djangotemplate
{% extends "base.html" %}

{% block script %}

    <div id="react">Loading...</div>

    <script>
      window.component = '{{ component }}';
      window.props = {{ props | json }};
      window.reactRoot = document.getElementById('react');
    </script>
    
{% endblock %}
```

And `base.html` that it extends:

```djangotemplate
<!DOCTYPE html>

<head>
    <title>{{ title }}</title>
</head>

<body>

    <h2>THIS LINE IS FROM BASE TEMPLATE</h2>
    
    {% block body %}
    {% endblock %}
    
</body>
```

The context's `component` and `props` are bound to `window.component` and `window.props` respectively.

Note the use of the `json` filter when setting `windows.props`! `{% load cra_helper_tags %}` provides this filter as a 
way to easily sanitize and convert a Python `dict` to a Javascript `Object`. The View context prepared above thus 
renders to the following typical Javascript Object:

```js
// This is what is returned in the rendered HTML
window.props = {"env": "Django"};
```
Finally, `window.reactRoot` specifies the container element that the React component should be rendered into. Setting a
value for this is only required if the container's `id` is *not* **"root"** (the same ID assigned to the container
`<div>` in the CRA project's `index.html`.)

> Note: you do not need to worry about JavaScript and CSS in React template. These will be injected automatically by 
`django-cra-helper`

### Using the template

To access `index.html` in a React app, use the template `<react-app-name>.html`:

```python
from django.shortcuts import render

# this function is registered to serve /
def index(request):
    context = {
        'component': 'App',
        'props': {
            'env': 'Django Index',
        },
        'title': 'Index page'
    }
    return render(request, 'react_index.html', context)

# this function is register to serve /user/<some number>
def user(request):
    context = {
        'component': 'App',
        'props': {
            'env': 'Django User'
        },
        'title': 'User'
    }
    return render(request, 'react_user.html', context)

```

#### Debug mode 

When the Django serer is started with `python mangage.py runserer` and `DEBUG == True`, it will check whether the React 
apps specified in `CRA_APPS` are running.

If it is, `django-cra-helper` will fetch html, js and css from that. Code changes in the React codebase will be updated 
immediately within Django views as well. 

> Note: the React apps live servers are independent of each other. You can let some live servers run while others do not.
In the later case, `django-cra-helper` falls to production mode on those apps.

Unlike version 1, there's no need to reload the page to see changes. But to enable this features, 3 paths are reserved
for this purpose: `/sockjs-node/*`, `/__webpack_dev_server__/*` and `/main.<hex-number>.hot-update.js`. If you happens
to use these paths, you can disable auto loading by setting `CRA_AUTO_RELOAD = False` in `settings.py`

#### Production mode

In production mode, `cra_helper.template_loader.ReactLoader` loads template from react app's `build/index.html`.

Hence, we need to run `npm run build` on react apps beforehand. Also, some small changes to `index.html` needs to be made
after building to make template inheritance works. 

`django-cra-helper` provides `buildreact` command to do just that.

```bash
python mangage.py buildreact
``` 

You can specify the apps to build. If none is provided, `buildreact` assumes that you want all of them.

```bash
python mangage.py buildreact react_index 
``` 

If `--collectstatic` is set, `collectstatic` command will be run after building.
