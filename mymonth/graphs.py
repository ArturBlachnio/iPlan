# todo - create proper classes
from datetime import date, timedelta
import pandas as pd
from bokeh.embed import components
from bokeh.models import ColumnDataSource, Range1d, NumeralTickFormatter, LinearAxis, LabelSet
from bokeh.plotting import figure, show, output_file

from mymonth.defaults import Defaults
from mymonth.datasets import DataSet


class MonthlyGraph:
    # todo - rename and move to graphs.py
    def __init__(self, db_table):
        self.db_table = db_table
        self.db_table_query_output = self.get_historical_data_from_db()
        self.df_days = self.convert_days_model_to_dataframe(self.db_table_query_output)
        self.df_months = self.get_summary_per_month(self.df_days)
        # Append current month summary
        self.df_months = self.df_months.append(self.get_summary_for_current_month())
        # Graph
        self.bokeh_monthly_components = self.get_monthly_graph_components(self.df_months)

    def get_historical_data_from_db(self, reference_date=None, display_years=2):
        # todo - move to datasets
        """Returns DataFrame with all entries between:
         - last day of previous month (selection=reference_date), and:
         - first day of current year - 'display_years'."""

        if reference_date is None:
            reference_date = date.today()

        query_last_date = date(reference_date.year, reference_date.month, 1) - timedelta(days=1)
        query_first_date = date(reference_date.year - display_years, 1, 1)
        query_output = self.db_table.query.filter(self.db_table.id.between(query_first_date, query_last_date)).all()
        return query_output

    @staticmethod
    def convert_days_model_to_dataframe(query_output):
        # todo - move to datasets and make it smarter
        """"Converts 'Days' query output into pandas DataFrame."""
        id = []
        ds = []
        dev = []
        pol = []
        ge = []
        crt = []
        hs = []
        alk = []
        for row in query_output:
            id.append(row.id)
            ds.append(row.ds)
            dev.append(row.dev)
            pol.append(row.pol)
            ge.append(row.ge)
            crt.append(row.crt)
            hs.append(row.hs)
            alk.append(row.alk)
        df = pd.DataFrame(data={'id': id, 'ds': ds, 'dev': dev, 'pol': pol, 'ge': ge, 'crt': crt, 'hs': hs, 'alk': alk})

        df.id = pd.to_datetime(df.id)
        # Fill nans
        columns_numerical = df.select_dtypes(include=['float64', 'int']).columns
        columns_timedelta = df.select_dtypes(include=['timedelta']).columns
        df[columns_timedelta] = df[columns_timedelta].fillna(timedelta())
        df[columns_numerical] = df[columns_numerical].fillna(0)
        return df

    @staticmethod
    def get_summary_per_month(df_days):
        # todo - move to datasets
        """Translates daily data into monthly summary"""
        df_days['month'] = df_days.id.dt.strftime('%ym%m')
        df_days['month_first_day'] = df_days.id
        df_days.alk.fillna(0, inplace=True)
        df_days.loc[(df_days.alk == 0), 'day0'] = 1
        df_days['ml'] = df_days.alk / 7.8 * 750
        df_days['productive_hrs'] = df_days.select_dtypes(include=['timedelta']).sum(axis=1)
        df_days.loc[df_days['productive_hrs'] == 0, 'productive_hrs'] = timedelta()
        df_days['target_hrs'] = df_days.id.map(Defaults.productive_hours_by_weekday)
        df_days['negative_hrs'] = (df_days['alk'] - 2.86).clip(0) * timedelta(minutes=20)

        df_month_score = df_days.groupby('month')[['productive_hrs', 'target_hrs', 'negative_hrs']].sum()
        df_month_score['score'] = (df_month_score.productive_hrs - df_month_score.negative_hrs) / df_month_score.target_hrs
        df_month_alk = df_days.groupby('month')[['day0', 'ml', 'id', 'month_first_day']].agg({'day0': sum, 'ml': sum, 'id': 'count', 'month_first_day': 'first'})
        df_months = df_month_score.join(df_month_alk)
        df_months['ml'] = df_months.ml / df_months.id
        df_months = df_months[['score', 'day0', 'ml', 'month_first_day']]
        return df_months

    def get_summary_for_current_month(self, reference_date=None):
        # todo - move to datasets
        """"Generates summary (score, days0 and ml) for current month"""
        if reference_date is None:
            reference_date = date.today()

        query_last_date = reference_date
        query_first_date = date(reference_date.year, reference_date.month, 1)
        query_output = self.db_table.query.filter(self.db_table.id.between(query_first_date, query_last_date)).all()

        df_days = self.convert_days_model_to_dataframe(query_output)
        df_months = self.get_summary_per_month(df_days)
        return df_months

    @staticmethod
    def get_monthly_graph_components(df_month):
        # todo - move to graphs
        df_month['labels_ml'] = df_month['ml'].astype(int).astype(str)
        df_month['labels_day0'] = df_month['day0'].astype(int).astype(str)
        df_month['ml_current'] = df_month['ml'].values[-1]
        df_month['ml_rank'] = df_month['ml'].rank().astype(int).map({1: '1st', 2: '2nd', 3: '3rd', 4: '4th', 5: '5th'}).fillna('')
        source = ColumnDataSource(df_month)
        plot = figure(title='Monthly summary',
                      x_range=source.data.get('month'),
                      y_range=Range1d(0, max(source.data.get('score')) * 1.1),
                      y_axis_label='Score [%]',
                      plot_width=600,
                      plot_height=400,
                      toolbar_location=None)

        plot.xaxis.major_label_orientation = 1
        plot.yaxis[0].formatter = NumeralTickFormatter(format='0%')

        plot.vbar(x='month', top='score', width=0.8, source=source, color=(100, 149, 237, 0.5), line_width=2)

        plot.extra_y_ranges['y_axis_ml'] = Range1d(0, max(source.data.get('ml')) * 1.05)
        axis_ml = LinearAxis(y_range_name="y_axis_ml", axis_label="Avg ml")
        plot.line(x='month', y='ml_current', y_range_name='y_axis_ml', source=source, line_color='maroon', line_width=0, line_dash='dotted')
        labels_ml_rank = LabelSet(x='month', y='ml', text='ml_rank', y_range_name='y_axis_ml', text_font_size='10px', text_color='gray', x_offset=-7, y_offset=-20, level='annotation', source=source, render_mode='canvas')
        plot.line(x='month', y='ml', y_range_name='y_axis_ml', source=source, line_color='maroon', line_width=2)
        plot.circle(x='month', y='ml', y_range_name='y_axis_ml', source=source, color="maroon", fill_color="white", size=7)
        labels_ml = LabelSet(x='month', y='ml', text='labels_ml', y_range_name='y_axis_ml', text_font_size='10px', text_color='maroon', x_offset=-3, y_offset=7, level='annotation', source=source, render_mode='canvas')

        plot.extra_y_ranges['y_axis_day0'] = Range1d(0, 50)
        plot.line(x='month', y='day0', y_range_name='y_axis_day0', source=source, line_color='gray', line_width=1)
        plot.circle(x='month', y='day0', y_range_name='y_axis_day0', source=source, color="gray", fill_color="white", size=7)
        labels_day0 = LabelSet(x='month', y='day0', text='labels_day0', y_range_name='y_axis_day0', text_font_size='10px', text_color='black', x_offset=-3, y_offset=5, level='annotation', source=source, render_mode='canvas')

        plot.add_layout(axis_ml, 'right')
        plot.add_layout(labels_ml)
        plot.add_layout(labels_day0)
        plot.add_layout(labels_ml_rank)
        return components(plot)


class Graph:
    @staticmethod
    def get_graph_components_tracking_daily_time(input_df):
        """Returns bokeh components for graph."""
        df = input_df.copy()
        source = ColumnDataSource(df)
        plot = figure(title='Tracking Hours',
                      y_range=source.data.get('date_str'),
                      x_axis_label='Actual work vs target [hrs]',
                      plot_width=400,
                      plot_height=400)

        plot.line(y='date_str', x='ds', source=source, line_color='#ccf1ff', line_width=3, legend_label='ds')
        plot.line(y='date_str', x='dev', source=source, line_color='#e4e8eb', line_width=3, legend_label='dev')
        plot.line(y='date_str', x='pol', source=source, line_color='antiquewhite', line_width=3, legend_label='pol')
        plot.line(y='date_str', x='ge', source=source, line_color='darkseagreen', line_width=3, legend_label='ge')
        plot.line(y='date_str', x='crt', source=source, line_color='lightblue', line_width=3, legend_label='crt')
        plot.line(y='date_str', x='hs', source=source, line_color='#ebc6c6', line_width=3, legend_label='hs')

        # display legend in top left corner (default is top right corner)
        plot.legend.location = "top_right"
        plot.legend.title = "Strategies:"
        plot.legend.background_fill_alpha = 0.2
        return components(plot)


""" # This is for testing
df = DataSet().tracking_df_daily_datetime
print(df)

source = ColumnDataSource(df)
plot = figure(title='Tracking Hours',
              y_range=source.data.get('date_str'),
              plot_width=400,
              plot_height=400)

plot.line(y='date_str', x='ds', source=source, line_color='#ccf1ff', line_width=3, legend_label='ds')
plot.line(y='date_str', x='dev', source=source, line_color='#e4e8eb', line_width=3, legend_label='dev')
plot.line(y='date_str', x='pol', source=source, line_color='antiquewhite', line_width=3, legend_label='pol')
plot.line(y='date_str', x='ge', source=source, line_color='darkseagreen', line_width=3, legend_label='ge')
plot.line(y='date_str', x='crt', source=source, line_color='lightblue', line_width=3, legend_label='crt')
plot.line(y='date_str', x='hs', source=source, line_color='#ebc6c6', line_width=3, legend_label='hs')

# display legend in top left corner (default is top right corner)
plot.legend.location = "top_left"
plot.legend.title = "Strategies"

output_file('test1.html')
show(plot)"""

