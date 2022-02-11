import os
import sys
import csv
import json
import subprocess
import pytz
from datetime import datetime
from dateutil import parser

# parameters
exclude_domains = [
    'www.google.com',
    'localhost',
    '192.168.',
]
dry_run = False

from params import *


''' get home directory '''
def get_home_dir():
    return os.path.expanduser('~')

''' list all google chrome profile directory '''
def list_chrome_profile(path):
    chrome_profile = []
    for root, dirs, files in os.walk(path):
        if 'History' in files:
            profile_name = os.path.basename(root)
            if profile_name in ['Default', 'System Profile', 'Guest Profile']:
                continue
            chrome_profile.append(root)
    return chrome_profile

''' list all history json file in specified path '''
def list_history_files(path):
    history_files = []
    for file in os.listdir(path):
        file_name = os.path.basename(file)
        if file_name.endswith('_history.json'):
            history_files.append(os.path.join(path, file))
    return history_files

''' parse history json file '''
def parse_history_file(history_file, browser, profile = 'Default'):
    with open(history_file, 'r') as f:
        history_data = json.load(f)
        # print(history_data)
    if not history_data:
        return

    # sort history by date
    history_data.sort(key=lambda x: x['LastVisitTime'], reverse=True)

    # get history within delta time
    for history in history_data:
        # parse isodate string
        visit_date = parser.parse(history['LastVisitTime'])
        visit_time = int(visit_date.strftime('%s'))
        local_time = visit_date.astimezone(tz).strftime("%Y/%m/%d %H:%M:%S")

        # stop parsing old history
        if visit_time < (now - delta):
            break
        
        # filter urls
        visit_url = history['Url']
        visit_title = history['Title']
        schema = visit_url.split('://')[0]
        # if schema in ['file', 'chrome', 'about', 'chrome-extension']:
        #     continue
        if not schema in ['http', 'https']:
            continue
        domain = visit_url.split('/')[2]
        domain = domain.split(':')[0]
        exclude = [item for item in exclude_domains if item in domain]
        if exclude:
            continue

        results.append({
            'browser': browser.replace('_', ' ').title(),
            'profile': profile,
            'domain': domain,
            'url': visit_url,
            'title': visit_title,
            'time': local_time,
            'visit_time': history['LastVisitTime'],
            'visit_count': history['VisitCount']
        })

        # print("%s | %s | %s\n%s" % (local_time, domain, visit_title, visit_url))


now = int(datetime.now(pytz.utc).strftime('%s'))
tz = '/'.join(os.path.realpath('/etc/localtime').split('/')[-2:])
tz = pytz.timezone(tz)
delta = 86400   # defaults to 1d

if len(sys.argv) > 1:
    arg = sys.argv[1]
    try:
        if arg.endswith('d'):
            delta = int(arg[:-1]) * 86400
        elif arg.endswith('h'):
            delta = int(arg[:-1]) * 3600
        elif arg.endswith('m'):
            delta = int(arg[:-1]) * 60
        else:
            delta = int(arg)
    except:
        delta = 0
if delta <= 0:
    print("Usage: python fetch.py 1d|6h|30m|3600")
    sys.exit(0)

print("Fetching last %d seconds of browser history." % delta)

# run hbd to get all history
results = []
FNULL = open(os.devnull, 'w')
if not dry_run:
    subprocess.call(['./hbd', '-f', 'json'], stdout=FNULL, stderr=FNULL)

# parse history json files
history_files = list_history_files('./results')
for history_file in history_files:
    browser = os.path.basename(history_file).split('_history.json')[0]
    parse_history_file(history_file, browser)

# run hbd with custom chrome profile dir
chrome_profiles_dir = list_chrome_profile(os.path.join(get_home_dir(), 'Library/Application Support/Google/Chrome'))
for profile in chrome_profiles_dir:
    profile_name = os.path.basename(profile)
    # print(profile_name)

    # get chrome account name from Preferences file
    # pref_file = os.path.join(profile, 'Preferences')
    # acc_info = None
    # with open(pref_file, 'r') as f:
    #     pref_data = json.load(f)
    #     if 'account_info' in pref_data and len(pref_data['account_info']) > 0:
    #         acc_info = pref_data['account_info'][0]
    # if acc_info:
    #     print("%s | %s | %s" % (profile_name, acc_info['full_name'], acc_info['email']))
    # continue
    
    # run hbd with profile as argument
    if not dry_run:
        subprocess.call(['./hbd', '-b', 'chrome', '-p', profile, '-f', 'json', '--dir', profile_name], stdout=FNULL, stderr=FNULL)

    # parse chrome_history.json file
    history_file = os.path.join(os.getcwd(), profile_name, 'chrome_history.json')
    parse_history_file(history_file, 'chrome', profile_name)

# sort results by visit time
results.sort(key=lambda x: x['visit_time'], reverse=True)

# print results
# results_by_domain = {}
# for data in results:
#     print("%s | %s - %s | %s | %s\n%s" % (
#         data['time'], data['browser'], data['profile'],
#         data['domain'], data['title'], data['url']
#     ))
#     domain = data['domain']
#     if not domain in results_by_domain:
#         results_by_domain[domain] = []
#     results_by_domain[domain].append([data['time'], data['browser'], data['profile'], data['title'], data['url']])

# write csv
# csv_name = os.path.join(os.getcwd(), 'results.csv')
# with open(csv_name, mode='w', encoding='UTF-8') as csv_out:
#     csv_writer = csv.writer(csv_out, delimiter=',', quotechar='"', lineterminator='\n', quoting=csv.QUOTE_MINIMAL)
#     # csv_writer.writerow(results[0].keys())
#     for row in results:
#         csv_writer.writerow(row)

# write js
js_name = os.path.join(os.getcwd(), 'data.js')
with open(js_name, mode='w') as f:
    f.write("var delta=%d,data=" % delta);
    json.dump(results, f)

print("Total %d histories found." % len(results))
# print(results_by_domain)

# open result page
subprocess.call(['open', 'results.html'], stdout=FNULL, stderr=FNULL)
