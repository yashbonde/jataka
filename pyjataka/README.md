# Jataka

Since NBX will eventually be using grafana for all it's dashboarding needs I think I will also use it from the starting stage itself. In order to install please check [here](https://grafana.com/docs/grafana/latest/installation/), on macos do the following.

## First Step

```bash
brew install grafana
brew services start grafana # starts in background
brew services stop grafana  # stop the background job
brew services list # list all the services running in the background
```

When `brew` is used to install `grafana`, the working directory is going to be `/opt/homebrew/Cellar/grafana/8.2.5`, check your version, I just had the latest. The paths now are realtive to above. By default, the configuration file is located at `.bottle/etc/grafana/grafana.ini`. For a Grafana instance installed using Homebrew, edit the `grafana.ini` file directly. Otherwise, (`share/grafana/conf/defaults.ini` has the default configuration DO NOT CHANGE IT) add a configuration file named `custom.ini` to the `conf/` folder to override any of the settings defined in `conf/defaults.ini`.

## In usage

The above instructions are good to just get started, but in practice you need to do the following:

1. Open `/opt/homebrew/etc/grafana/grafana.ini` and go `[paths]` section and add the following in it `plugins = "/path/to/grafana-plugins"`
2. To create a new plugin do the following:
```
# this will git clone the template and it will require a bunch input
# remember the id, in my case it is 'nbx-gpect'
npx @grafana/toolkit plugin:create my-plugin

# go into the folder
cd my-plugin

# https://github.com/grafana/grafana/issues/40764
# because there is version mismatch problem
rm yarn.lock

# install the requirements
yarn install
yarn dev

# Grafana requires the signed plugin but, so for development you
# need to set env variable GF_PLUGINS_ALLOW_LOADING_UNSIGNED_PLUGINS
# with the id of the plugin
GF_PLUGINS_ALLOW_LOADING_UNSIGNED_PLUGINS=nbx-gpect grafana-server \
--config /opt/homebrew/etc/grafana/grafana.ini \
--homepath /opt/homebrew/opt/grafana/share/grafana

# if the above doesn't work try setting allow_loading_unsigned_plugins=true
# in /opt/homebrew/etc/grafana/grafana.ini
```

* Configuration [documentation](https://grafana.com/docs/grafana/latest/administration/configuration/).
* Creating a new plugin [documentation](https://grafana.com/tutorials/build-a-data-source-plugin/#create-a-new-plugin)

## Filling Database

Instead of running a thrasher to fill the database I am using an actual model, you can go to `jobs/` folder to see the scripts.
