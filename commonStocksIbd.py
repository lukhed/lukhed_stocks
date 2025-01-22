from resources.aceCommon import osCommon as osC
from resources.aceCommon import fileCommon as fC
from resources.aceCommon import requestsCommon as rC
from resources.aceCommon import timeCommon as tC
import commonDataManagement
from typing import Optional


class IBD:
    def __init__(self):
        self.dm = commonDataManagement.DataManagement()
        self.default_cache_loc = osC.create_file_path_string(['resources', 'grindSundayStocks',
                                                              'ibd-industry-group-rankings'])
    @staticmethod
    def get_industry_group_rankings_table(provide_date=None, date_input_format="%Y%m%d"):
        def _table_try_except(v):
            v = v.replace("+", "")
            try:
                return False, float(v)
            except:
                return True, v

        if provide_date is None:
            url_time = tC.create_time_stamp_new("%b-%d-%Y")
        else:
            url_time = tC.convert_date_format(provide_date, date_input_format, to_format="%b-%d-%Y")

        url = f'https://www.investors.com/data-tables/industry-group-rankings-{url_time}/'
        headers = {
            "authority": "www.investors.com",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,"
                      "*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "max-age=0",
            "upgrade-insecure-requests": "1",
        }

        retries = 5
        while retries > 0:
            if retries != 5:
                tC.sleep(10)

            request_get = rC.basic_request(url, add_user_agent=True, headers=headers)
            soup = rC.get_soup_from_page(request_get)

            try:
                table = rC.soup_find_all_classes_in_soup(soup, "table", "table")[0]
                break
            except:
                print("IBD rejected request, waiting 10 seconds and trying another user agent")
            retries = retries - 1

        table_data = []
        counter = 0
        for row in table.find_all('tr'):
            cells = row.find_all('td')
            row_data = [cell.get_text(strip=True) for cell in cells]
            if counter != 0:
                e0, c0 = _table_try_except(row_data[0])
                e1, c1 = _table_try_except(row_data[1])
                e2, c2 = _table_try_except(row_data[2])
                c3 = row_data[3]
                e4, c4 = _table_try_except(row_data[4])
                e5, c5 = _table_try_except(row_data[5])
                e6, c6 = _table_try_except(row_data[6])
                error = e0 and e1 and e2 and e4 and e5 and e6
                row_data = [c0, c1, c2, c3, c4, c5, c6, error]
            else:
                row_data.append("error converting")

            table_data.append(row_data.copy())
            counter = counter + 1

        return table_data

    @staticmethod
    def screener_weekly_review():
        url = 'https://ibdstockscreener.investors.com/research-tool/api/ibdlist/get/_YourWeeklyReview'
        r = rC.use_requests_return_json(url, add_user_agent="yes")
        stop = 1

    def load_industry_group_rankings_from_cache(self, specify_cache_location=False, start_date=None, end_date=None,
                                                date_format="%Y%m%d"):
        cache = specify_cache_location if specify_cache_location else self.default_cache_loc
        data = self.dm.load_json_files_from_dir(specify_full_path=cache, find_add_date_attribute=True)

        if start_date:
            # Filter out stuff before start_date
            start_date = tC.convert_date_format(start_date, date_format=date_format, to_format="%Y%m%d")
            data = [x for x in data if tC.check_if_date_time_string_is_in_given_range(x['date'], start_date,
                                                                                      "50000101",
                                                                                      input_format="%Y%m%d")]

        if end_date:
            # Filter out stuff after end_date
            end_date = tC.convert_date_format(end_date, date_format=date_format, to_format="%Y%m%d")
            data = [x for x in data if tC.check_if_date_time_string_is_in_given_range(x['date'], "19000101",
                                                                                      end_date,
                                                                                      input_format="%Y%m%d")]

        return data


def test_load_group_rankings():
    fp = osC.create_dir_path_to_programming()
    dir_list = ['grindSundayStocks', 'resources', 'grindSundayStocks', 'ibd-industry-group-rankings']
    fp = osC.append_to_dir(fp, dir_list, list=True)

    rankings = ibd.load_industry_group_rankings_from_cache(specify_cache_location=fp)
    stop = 1
    rankings = ibd.load_industry_group_rankings_from_cache(specify_cache_location=fp, start_date="20240601",
                                                           end_date='20240630')
    stop = 1

def test_get_group_rankings():
    ibd.get_industry_group_rankings_table()

def main():
    test_load_group_rankings()
    stop = 1


if __name__ == '__main__':
    ibd = IBD()
    main()
