# Nginx Proxied Site

Configure Nginx proxying for a site. This role only creates one config in `/etc/nginx/conf.d` and optionally creates cache directories for it, but **does not** verify or reload Nginx configuration. You are supposed to do it in a handler of the parent role or play.

## Role Variables

Only one dictionary is required: `site`. The rest of the variables are optional.

### Members of `site` Dictionary

The following members can only appear in `site` dictionary, but not locations (see below).

#### `names`

Required. A list of [domains, wildcards, or regexes](http://nginx.org/en/docs/http/ngx_http_core_module.html#server_name), by which server will respond. Those are canonical names of the site causing Nginx to serve site content, not redirect elsewhere. The first name in the list will be considered the *primary* name, see the next member. Primary name may start with a dot: `.example.org`.

#### `redirect_from`

Required. A list of [domains, wildcards, or regexes](http://nginx.org/en/docs/http/ngx_http_core_module.html#server_name), which will return permanent redirect to the *primary* name as noted above.

#### `ssl`

Optional. Turns SSL on or off.

Default: true

#### `ssl_key` and `ssl_cert`

Optional, but both must be either present or absent. Set [`ssl_certificate_key`](http://nginx.org/en/docs/http/ngx_http_ssl_module.html#ssl_certificate_key) and [`ssl_certificate`](http://nginx.org/en/docs/http/ngx_http_ssl_module.html#ssl_certificate), respectively.

#### `allow_robots`

Optional. If false, will generate a location for `/robots.txt` that disallows crawling to all user agents.

Default: true

#### `referrer_spammers`

Optional. A dictionary of domains (without leading dots) which are known [referral spammers](https://en.wikipedia.org/wiki/Referrer_spam). Requests with these referrers will receive 403 Forbidden status.

#### `caches`

Optional. A list of dictionaries, defining [cache zones](http://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_cache_path). Members of each dictionary:

* `id` - required, defines the name of the key zone; cacheable locations will refer to caches by this field.

* `max_keys` - required, estimated number of keys in the zone; used to calculate zone size: "one megabyte zone can store about 8 thousand keys".

* `max_size` - optional, maximum size of cache in Nginx units (e.g. *5g*).

* `inactive` - optional, maximum lifetime of valid cache objects, that don't get accessed, in Nginx units (e.g. *4h*).

#### `locations`

Optional. A list of locations as dictionaries which can be nested infinitely (limits of the Universe still apply).

### Members Applicable Only to Locations

#### `location`

Required. [The URI of the location](http://nginx.org/en/docs/http/ngx_http_core_module.html#location), e.g. `/` or `\.jpe?g$`. Remember to properly escape your regexes for the YAML parser.

#### `operator`

Optional. Matching operator of the location, e.g. `=` or `~*`. Remember YAML quoting.

Default: "" (empty string, or prefix location match)

### Members Applicable to Both `site` and Locations

#### `gzip`

Optional. Controls [compression](http://nginx.org/en/docs/http/ngx_http_gzip_module.html#gzip) at server or location level. If undefined, no directive will be added (inherit from parent block). Note that other GZIP settings are not managed by this role, and should be inherited from `http` block.

Default: undefined

#### `client_max_body_size`

Optional. Sets the [maximum size of request body](http://nginx.org/en/docs/http/ngx_http_core_module.html#client_max_body_size) in Nginx units, e.g. *1m*.

Default: undefined

#### `htpasswd`

Optional. If set, defines the path to [htpasswd file](http://nginx.org/en/docs/http/ngx_http_auth_basic_module.html#auth_basic_user_file), absolute or relative to `/etc/nginx`. This enables HTTP Basic Authentication. Currently, there's no way to disable inherited (nested) Basic Auth setting with this role.

#### `proxy`

Optional. A dictionary controlling proxy behavior. Possible members described below.

##### `proxy.pass`

Optional. Inserts a [`proxy_pass` directive](http://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_pass). Type: string.

##### `proxy.redirect`

Optional dictionary of two string members: `from` and `to`. Inserts a [`proxy_redirect` directive](http://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_redirect).

##### `proxy.headers`

Optional. A dictionary with three optional members:

* `set` - a dictionary where keys are header names. Inserts [`proxy_set_header` directives](http://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_set_header), i.e. headers sent to the backend in each request.

* `hide` - a list of header names removed from the backend response, and not passed to the client. Produces [`proxy_hide_header` directives](http://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_hide_header).

* `ignore` - a list of header names; inserts a [`proxy_ignore_headers` directive](http://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_ignore_headers) to disable certain processing logic.

#### `cache`

Optional. Controls caching at the block level and below. If undefined, no caching directives will be produced. Possible members:

* `enabled` - boolean, defaults to *true*. Inserts [`proxy_cache`](http://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_cache) and [`proxy_cache_valid`](http://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_cache_valid) directives. If set to *true*, then the members `id` and `duration` are required.

* `id` - string, required if `enabled` is *true*. Uses the cache zone with this name.

* `duration` - caching time in Nginx units; produces the [`proxy_cache_valid` directive](http://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_cache_valid). May be used to configure response code as well: `200 302 10m`.

#### `cors`

Optional. If defined, this dictionary generates an `if` block to handle [CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS) OPTIONS request. The dictionary members are:

* `origin` - string, defaults to `*`; sets the value of [Access-Control-Allow-Origin](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Allow-Origin).

* `max_age` - optional integer producing the [Access-Control-Max-Age header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Max-Age). If undefined, no header will be sent.

* `methods` - an optional list of permitted methods for the [Access-Control-Allow-Methods header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Allow-Methods).

* `headers` - an optional list of permitted headers, as in [Access-Control-Allow-Headers header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Allow-Headers).

### Optional Variables

#### `ngxs_config_dir`

Nginx configuration include directory.

Default: `/etc/nginx/conf.d`

#### `ngxs_cache_dir`

Root directory for Nginx caches

Default on all platforms: `/var/cache/nginx`

#### `ngxs_cache_dir_owner`, `ngxs_cache_dir_group`

Owner and group of the cache directory.

Defaults:

* RedHat: `nginx`

* Debian: `www-data`

## Example Playbook: Simple Site

    ---
    - hosts: nginx-prod
      tasks:
        - name: Configure a simple site
          include_role:
            name: devgateway.nginx-proxied-site
          vars:
            site:
              names:
                - info.example.net
              redirect_from:
                - information.example.net
              locations:
                - location: /
                  proxy:
                    pass: http://tomcat:8081/info

## Example Playbook: Complex Site

    ---
    - hosts: nginx-prod
      tasks:
        - name: Configure a complex site
          include_role:
            name: devgateway.nginx-proxied-site
          vars:
            site:
              names:
                - .customers.example.org
              redirect_from:
                - .clients.example.org
                - ~(beta|prod)\.example\.(org|net)$
              ssl: true
              ssl_key: /etc/pki/tls/private/site.pem
              ssl_cert: /etc/pki/tls/certs/site.crt
              allow_robots: false
              referrer_spammers:
                - mallory.example.net
              caches:
                - id: java
                  max_keys: 160000
                  max_size: 1g
                  inactive: 1h
              client_max_body_size: 24m
              gzip: true
              proxy:
                headers:
                  set:
                    Host: $http_host
                    X-Real-IP: $remote_addr
                    X-Forwarded-For: $proxy_add_x_forwarded_for
                    X-Forwarded-Proto: $scheme
                  ignore:
                    - Set-Cookie
                    - Vary
                  hide:
                    - X-AMZ-Request-ID
              locations:
                - location: /
                  proxy:
                    pass: http://tomcat:8080/foo
                    redirect:
                      from: http://$proxy_host/foo
                      to: $scheme://$server_name
                    headers:
                      set:
                        X-Secure: very
                  locations:
                    - location: /widgets
                      cors:
                        max_age: 1728000
                        methods:
                          - GET
                          - POST
                          - PUT
                          - DELETE
                          - OPTIONS
                        headers:
                          - X-Requested-With
                          - X-HTTP-Method-Override
                          - Content-Type
                          - Accept
                          - Origin
                      cache:
                        id: java
                        duration: 1h
                        key: $request_uri
                      locations:
                        - location: /widgets/update.do
                          operator: "="
                          cache:
                            enabled: false
                - location: /ci
                  htpasswd: jenkins.txt
                  proxy:
                    pass: http://build:8080/jenkins/
                    redirect:
                      from: http://$proxy_host/jenkins
                      to: $scheme://$server_name/ci

## License

GPLv3+

## Author Information

2018, Development Gateway