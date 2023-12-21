# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.16.0
#   kernelspec:
#     display_name: Python 3
#     name: python3
# ---

# + [markdown] id="83PUTwFvB2gE"
# # Using CrUX data for better performance visualization

# + id="Tz0XM8bHp5Yn" executionInfo={"status": "ok", "timestamp": 1702977194238, "user_tz": -540, "elapsed": 4, "user": {"displayName": "", "userId": ""}}
import pandas as pd
import decimal

# + id="bIw82qhuHWy0" colab={"base_uri": "https://localhost:8080/", "height": 81, "referenced_widgets": ["028a018605ae481686e8a0434a5fe482", "50f4a3855aa442ec9c9d3239d6dafe04", "82340ccf735844f08659d12cce652344", "1a2d8a2f36a343e2b1936582f65118ea", "89bf74204dd646c888f62250d311f7e5", "1ea97c86257241af9d9fa4462ed82061", "52d33f6c9a924defbc5c5cb7be42e907", "d9f40e0ff54942c99c1683e07f60c36c", "919d6e404f1947c1bbc94592fbed1e96", "b1315c05ac9d43f5807f7d6b4fbfd1c0", "891df5a944cd48de80756b88f8b53002", "7642f79ab65c4090a298d86fb02fb51d", "3b4a07282068431bb693baa3385d3e7c", "c198e1ef5a664733a845463ce31d75d5", "8c30e0db3510429b8449e8152abbad89", "d278584d9a4d4f2190f8b24769bcc6c7", "845b1282014d431488549abe4dcbf0ff", "da15e668f10e40af8d447d1b622a49a0", "68efc9a32cbb43b886eae79100d7de04", "2503a4dcc665459ebd40e2c52c475676", "6584bc3591644c2c852155b0f4037492", "3078430bcbfb4e32b86d9e9785237405"]} executionInfo={"status": "ok", "timestamp": 1702977324078, "user_tz": -540, "elapsed": 4167, "user": {"displayName": "", "userId": ""}} outputId="ad0c2ac2-f873-4688-aa15-479a44f5db37"
# %%bigquery results --project tai-test

SELECT * FROM `chrome-ux-report.country_jp.202311` WHERE origin = 'https://www.akamai.com'

# + id="itFJzBFNr72l" colab={"base_uri": "https://localhost:8080/", "height": 337} executionInfo={"status": "ok", "timestamp": 1702977326063, "user_tz": -540, "elapsed": 147, "user": {"displayName": "", "userId": ""}} outputId="0505d07b-09d0-487e-bf94-a4e661dfe130"
results.head()


# + colab={"base_uri": "https://localhost:8080/", "height": 256} id="U22yYfZRvx8o" executionInfo={"status": "ok", "timestamp": 1702977329462, "user_tz": -540, "elapsed": 172, "user": {"displayName": "", "userId": ""}} outputId="299606ae-7ba3-4726-b292-ce3f4903a94f"
def find_histogram(df, hist=None):
  """Find histogram within GBQ CrUX dataset"""
  if not hasattr(df, 'keys'): return
  if hist is None: hist = []

  for i in df.keys():
    if i == 'histogram':
      # create label name from access path
      col = "_".join([i for i in hist if type(i) is str])
      yield col, pd.DataFrame.from_records(df[i]['bin'])
      return

    # dig deeper
    hist.append(i)
    yield from find_histogram(df[i], hist)
    hist.pop()

def get_histogram(results):
  """Returns a clean dataframe from histograms in CrUX data"""

  # merge all histograms into one dataframe
  def find_histogram_wrapper(results):
    for i, df in find_histogram(results):
      df.columns = ['start', 'end', i + "_rv"] # RV for Raw Value
      yield df
  df = pd.concat(find_histogram_wrapper(results))

  # fix start/end as some use Decimal seconds while other use milliseconds
  df['start'] = df.start.apply(lambda v: int(v * 1000) if type(v) is decimal.Decimal else v)
  df['end'] = df.end.apply(lambda v: int(v * 1000) if type(v) is decimal.Decimal else v)

  # merge probability data for each start-end range
  df = df.groupby(['start', 'end']).sum().reset_index()

  # add a helper column useful for filtering in later stage
  df['step'] = df.end - df.start

  # add a CDF value column for each performance data (for easier plotting)
  df.sort_values('end', inplace=True)
  for i in df.columns:
    if i.endswith('_rv'):
      df[i.replace('_rv', '')] = df[i].cumsum()
  return df

df = get_histogram(results)
df.head()

# + id="7vAVyWp-hikK" colab={"base_uri": "https://localhost:8080/", "height": 472} executionInfo={"status": "ok", "timestamp": 1702977331346, "user_tz": -540, "elapsed": 645, "user": {"displayName": "", "userId": ""}} outputId="59fcd90c-d3cb-43dd-9b82-ef995f0a3d3b"
df.plot(y='first_paint', x='end', xlim=[0, 5000], ylim=[0, 1.0])

# + colab={"base_uri": "https://localhost:8080/", "height": 1000} id="9UpH0D3x8eX7" executionInfo={"status": "ok", "timestamp": 1702977332432, "user_tz": -540, "elapsed": 170, "user": {"displayName": "", "userId": ""}} outputId="dfdd6fde-2248-4113-e361-243dc779fc3d"
df[['step', 'end', 'first_paint']].head(50)

# + colab={"base_uri": "https://localhost:8080/", "height": 472} id="vL8a8MhF_C6X" executionInfo={"status": "ok", "timestamp": 1702977333697, "user_tz": -540, "elapsed": 320, "user": {"displayName": "", "userId": ""}} outputId="c7d00910-7637-4c24-ba54-8a9a212e2cd7"
df[df.step == 100].plot(y='first_paint', x='end', xlim=[0, 5000], ylim=[0, 1.0])

# + id="ULx7bAuqhipp" colab={"base_uri": "https://localhost:8080/", "height": 489} executionInfo={"status": "ok", "timestamp": 1702977334726, "user_tz": -540, "elapsed": 601, "user": {"displayName": "", "userId": ""}} outputId="25d8ac6d-c302-4503-d5e3-6ca68e1308ac"
ax = df[df.step == 100].plot(y='experimental_time_to_first_byte', x='end', xlim=[0, 10000], ylim=[0, 1.0])
df[df.step == 100].plot(y='first_contentful_paint', x='end', ax=ax)
df[df.step == 100].plot(y='dom_content_loaded', x='end', ax=ax)
df[df.step == 100].plot(y='largest_contentful_paint', x='end', ax=ax)
df[df.step == 25].plot(y='first_input_delay', x='end', ax=ax)
df[df.step == 25].plot(y='interaction_to_next_paint', x='end', ax=ax)
df[df.step == 100].plot(y='onload', x='end', ax=ax)

# annotate with AxesSubplot methods
ax.legend(loc='lower right', bbox_to_anchor=(1.0, 0.0))
ax.grid()
ax.set_ylabel('percentile (1.0=100%)')
ax.set_xlabel('time[ms]')
ax.set_title('Timing Distribution')


# + id="ra_EA1fPrlNo"


# + id="Ev1D9QkjrlSt" colab={"base_uri": "https://localhost:8080/", "height": 403} executionInfo={"status": "ok", "timestamp": 1702890351433, "user_tz": -540, "elapsed": 207, "user": {"displayName": "", "userId": ""}} outputId="f2224b4c-e5e2-4f83-f802-7c9149b6cee3"

