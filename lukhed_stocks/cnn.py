from lukhed_basic_utils import requestsCommon as rC
from lukhed_basic_utils import timeCommon as tC

class CNN:

    def get_major_indices(self, date_str=None):
        d = tC.create_timestamp(output_format="%Y-%m-%d") if date_str is None else date_str
        url = f'https://production.dataviz.cnn.io/markets/index/DJII-USA,SP500-CME,COMP-USA,RUT-RUX,VIX-CBO:D/{d}'
        data = rC.request_json(url, add_user_agent=True)
        return data