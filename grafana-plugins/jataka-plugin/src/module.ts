import { DataSourcePlugin } from '@grafana/data';
import { DataSource } from './datasource';
import { DataSource2 } from './ds2';
import { ConfigEditor } from './ConfigEditor';
import { QueryEditor } from './QueryEditor';
import { MyQuery, MyDataSourceOptions } from './types';

// The query method is the heart of any data source plugin. It accepts a query from the user,
// retrieves the data from an external database, and returns the data in a format that Grafana
// recognizes.
export const plugin = new DataSourcePlugin<DataSource, MyQuery, MyDataSourceOptions>(DataSource)
  .setConfigEditor(ConfigEditor)
  .setQueryEditor(QueryEditor);

export const plugin2 = new DataSourcePlugin<DataSource2, MyQuery, MyDataSourceOptions>(DataSource2)
  .setConfigEditor(ConfigEditor)
  .setQueryEditor(QueryEditor);
