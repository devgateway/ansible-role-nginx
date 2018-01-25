# Nginx Proxied Site

Configure Nginx proxying for a site. This role only creates one config in `/etc/nginx/conf.d` and optionally creates cache directories for it, but **does not** verify or reload Nginx configuration. You are supposed to do it in a handler of the parent role or play.

## Role Variables

Only one dictionary is required: `site`. The rest of the variables are optional.

### Members of `site` Dictionary

The following members can only appear in `site` dictionary, but not locations (see below).

#### `names`

Required. A list of [domains, wildcards, or regexes](http://nginx.org/en/docs/http/ngx_http_core_module.html#server_name), by which server will respond. Those are canonical names of the site causing Nginx to serve site content, not redirect elsewhere. The first name in the list will be considered the *primary* name, see the next member.

#### `redirect_from`

Required. A list of [domains, wildcards, or regexes](http://nginx.org/en/docs/http/ngx_http_core_module.html#server_name), which will return permanent redirect to the *primary* name as noted above.

#### `ssl`

Optional. Turns SSL on or off.

Default: true.

#### `ssl_key` and `ssl_cert`

Optional, but must be both present or absent. Set [`ssl_certificate_key`](http://nginx.org/en/docs/http/ngx_http_ssl_module.html#ssl_certificate_key) and [`ssl_certificate`](http://nginx.org/en/docs/http/ngx_http_ssl_module.html#ssl_certificate), respectively.

#### `allow_robots`

Optional. If false, will generate a location for `/robots.txt` that disallows crawling to all user agents.

Default: true

#### `caches`

Optional. A list of dictionaries, defining [cache zones](http://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_cache_path). Members of each dictionary:

* `id` - required, defines the name of the key zone; cacheable locations will refer to caches by this field.

* `max_keys` - required, estimated number of keys in the zone; used to calculate zone size: "one megabyte zone can store about 8 thousand keys".

* `max_size` - optional, maximum size of cache in Nginx units (e.g. *5g*).

* `inactive` - optional, maximum lifetime of valid cache objects, that don't get accessed, in Nginx units (e.g. *4h*).

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

## Example Playbook


## License

GPLv3+

## Author Information

2018, Development Gateway
