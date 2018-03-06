# devgateway.nginx

This is a low-level utility role to configure Nginx daemon *or* an individual site (`server` block and related directives).

In a nutshell, this role translates YAML structures of certain grammar into Nginx grammar. Invoke this role (which knows *how* to generate Nginx syntax) from a higher level role (which knows *what* to generate). For example:

    - name: Configure a PHP site
      include_role:
        name: devgateway.nginx
        tasks_from: site
      vars:
        site:
          server: 
            include: fastcgi_params
            fastcgi_index: index.php
            server_name: "{{ server_name }}"
            listen: "{{ ssl | default(true) | ternary(443, 80) }}"
            ssl: "{{ ssl }}"

Thus, this role provides two independent modes:

* daemon configuration which configures `nginx.conf` using `tasks_from: nginx`, and
* site configuration which configures `conf.d/`*`site`*`.conf` using `tasks_from: site`.

These two are shipped in a single role, because they share a Jinja2 macro library for Nginx grammar.

The role grammar is based on [Nginx configuration *contexts*](http://nginx.org/en/docs/beginners_guide.html#conf_structure). Either mode takes just one dictionary, which contains:

* Nginx directives applicable in current context and their values, as described below, and
* other contexts, potentially nested, with their directives and values.

**Be advised**, that although this role is idempotent, it operates on templates, and thus, on entire files, not individual directives. If you manually add a directive to the target file, it will be overwritten.

## Daemon Configuration Mode (`nginx.conf`)

This mode uses a dictionary called `ngx_settings`, representing `main` context. All members are optional. Possible nested contexts:

* `events`
* `http`

## Site Configuration Mode (`conf.d/`*`site`*`.conf`)
