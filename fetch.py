import os
import sys
import json
import subprocess
from datetime import datetime

# parameters
exclude_domains = [
    'www.google.com',
    'localhost',
    '192.168.',
]
dry_run = False
dump_mode = False
delta = 86400   # defaults to 1d

from params import *
if os.getenv("DRY_RUN"):
    dry_run = True


''' get home directory '''
def get_home_dir():
    return os.path.expanduser('~')

''' list all google chrome profile directory '''
def list_chrome_profile(path):
    chrome_profile = []
    if os.path.exists(path):
        for root, dirs, files in os.walk(path):
            if 'History' in files:
                profile_name = os.path.basename(root)
                if profile_name in ['Default', 'System Profile', 'Guest Profile']:
                    continue
                chrome_profile.append(root)
    return chrome_profile

def list_incogniton_profile(path):
    incogniton_profile = []
    if os.path.exists(path):
        for root, dirs, files in os.walk(path):
            if 'Default' in dirs:
                incogniton_profile.append(os.path.join(root, 'Default'))
    return incogniton_profile

''' list all history json file in specified path '''
def list_history_files(path):
    history_files = []
    if os.path.exists(path):
        for file in os.listdir(path):
            file_name = os.path.basename(file)
            if file_name.endswith('_history.json'):
                history_files.append(os.path.join(path, file))
    return history_files

''' add profile info and print to stdout '''
def add_profile_info(browser, profile = 'Default', acc_info = {}):
    full_name = acc_info.get('full_name')
    email = acc_info.get('email')
    profile_info = {
        'browser': browser,
        'profile': profile,
        'full_name': full_name,
        'email': email
    }
    profile_data.append(profile_info)
    print("%s | %s | %s | %s" % (browser, profile, full_name, email))

''' parse history json file '''
def parse_history_file(history_file, browser, profile = 'Default', acc_info = {}):
    if not os.path.exists(history_file):
        return
    with open(history_file, 'rb') as f:
        history_data = json.load(f)
        # print(history_data)
    if not history_data:
        return
    if dump_mode:
        return

    # sort history by date
    history_data.sort(key=lambda x: x['LastVisitTime'], reverse=True)

    # get history within delta time
    for history in history_data:
        # parse isodate string
        try:
            visit_date = parser.parse(history['LastVisitTime'])
        except:
            continue

        # stop parsing old history
        if (now - visit_date).total_seconds() > delta:
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

        if sys.version_info[0] < 3:
            # Python 2.x, Only work on Unix compatible OSes
            try:
                tz = '/'.join(os.path.realpath('/etc/localtime').split('/')[-2:])
                tz = pytz.timezone(tz)
                local_time = visit_date.astimezone(tz).strftime("%Y/%m/%d %H:%M:%S")
            except:
                local_time = visit_date.strftime("%Y/%m/%d %H:%M:%S UTC")
        else:
            local_time = visit_date.astimezone().strftime("%Y/%m/%d %H:%M:%S")

        results.append({
            'browser': browser,
            'profile': profile,
            'full_name': acc_info.get('full_name'),
            'email': acc_info.get('email'),
            'domain': domain,
            'url': visit_url,
            'title': visit_title,
            'time': local_time,
            'visit_time': history['LastVisitTime'],
            'visit_count': history['VisitCount']
        })

        # print("%s | %s | %s\n%s" % (local_time, domain, visit_title, visit_url))


if len(sys.argv) > 1:
    arg = sys.argv[1]
    if arg == "dump":
        dump_mode = True
    else:
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

if not dump_mode:
    print("Fetching last %d seconds of browser history." % delta)
    import pytz
    from dateutil import parser
    now = datetime.now(pytz.utc)

# run hbd to get all history
results = []
profile_data = []
FNULL = open(os.devnull, 'w')
BASEDIR = os.path.dirname(os.path.realpath(__file__))
HBD = os.path.join(BASEDIR, 'hbd.exe' if sys.platform == 'win32' else 'hbd')
if not dry_run:
    subprocess.call([HBD, '-f', 'json'], stdout=FNULL, stderr=FNULL)

# parse history json files
history_files = list_history_files('./results')
for history_file in history_files:
    browser = os.path.basename(history_file).split('_history.json')[0]
    browser = browser.replace('_', ' ').title()
    add_profile_info(browser)
    if not dump_mode:
        parse_history_file(history_file, browser)

# run hbd with custom chrome profile dir
if sys.platform == 'darwin':
    chrome_profiles_dir = list_chrome_profile(os.path.join(get_home_dir(), 'Library', 'Application Support', 'Google', 'Chrome'))
elif sys.platform == 'linux':
    chrome_profiles_dir = list_chrome_profile(os.path.join(get_home_dir(), '.config', 'google-chrome'))
elif sys.platform == 'win32':
    chrome_profiles_dir = list_chrome_profile(os.path.join(os.environ.get('LOCALAPPDATA'), 'Google', 'Chrome', 'User Data'))
else:
    chrome_profiles_dir = []
for profile in chrome_profiles_dir:
    profile_name = os.path.basename(profile)
    # print(profile_name)

    # get chrome account name from Preferences file
    pref_file = os.path.join(profile, 'Preferences')
    if not os.path.isfile(pref_file):
        continue
    if not os.path.isdir(profile_name):
        os.mkdir(profile_name)
    if sys.platform == 'win32':
        os.system('copy /y "%s" "%s/" >NUL' % (pref_file, profile_name))
    else:
        os.system('cp "%s" "./%s/"' % (pref_file, profile_name))
    acc_info = {}
    with open(pref_file, 'r') as f:
        try:
            pref_data = json.load(f)
            if 'account_info' in pref_data and len(pref_data['account_info']) > 0:
                acc_info = pref_data['account_info'][0]
        except:
            pass
    
    # copy bookmarks, history, cookies, etc
    for file_name in ['Bookmarks', 'History', 'Cookies', 'Login Data', 'Login Data For Account', 'Secure Preferences']:
        file_path = os.path.join(profile, file_name)
        if os.path.exists(file_path):
            if sys.platform == 'win32':
                os.system('copy /y "%s" "%s/" >NUL' % (file_path, profile_name))
            else:
                os.system('cp "%s" "./%s/"' % (file_path, profile_name))
    
    # run hbd with profile as argument
    if not dry_run:
        subprocess.call([HBD, '-b', 'chrome', '-p', profile, '-f', 'json', '--dir', profile_name], stdout=FNULL, stderr=FNULL)

    browser = 'Chrome'
    add_profile_info(browser, profile_name, acc_info)
    
    if not dump_mode:
        # parse chrome_history.json file
        history_file = os.path.join(os.getcwd(), profile_name, 'chrome_history.json')
        parse_history_file(history_file, browser, profile_name, acc_info)

# run hbd with incogniton profile dir
if sys.platform == 'darwin':
    incogniton_profiles_dir = list_incogniton_profile(os.path.join(get_home_dir(), 'Library', 'Application Support', 'Incogniton', 'config'))
elif sys.platform == 'win32':
    incogniton_profiles_dir = list_incogniton_profile(os.path.join(os.environ.get('APPDATA'), 'Incogniton', 'Incogniton', 'config'))
else:
    incogniton_profiles_dir = []
for profile in incogniton_profiles_dir:
    profile_name = os.path.basename(os.path.dirname(profile))
    # print(profile_name)

    # get profile name from Preferences file
    pref_file = os.path.join(profile, 'Preferences')
    if not os.path.isfile(pref_file):
        continue
    if not os.path.isdir(profile_name):
        os.mkdir(profile_name)
    if sys.platform == 'win32':
        os.system('copy /y "%s" "%s/" >NUL' % (pref_file, profile_name))
    else:
        os.system('cp "%s" "./%s/"' % (pref_file, profile_name))
    acc_info = {}
    with open(pref_file, 'r') as f:
        try:
            pref_data = json.load(f)
            if 'profile' in pref_data and len(pref_data['profile']) > 0:
                acc_info['full_name'] = pref_data['profile']['name']
        except:
            pass
    
    # copy bookmarks, history, cookies, etc
    for file_name in ['Bookmarks', 'History', 'Cookies', 'Login Data', 'Login Data For Account', 'Secure Preferences']:
        file_path = os.path.join(profile, file_name)
        if os.path.exists(file_path):
            if sys.platform == 'win32':
                os.system('copy /y "%s" "%s/" >NUL' % (file_path, profile_name))
            else:
                os.system('cp "%s" "./%s/"' % (file_path, profile_name))
    
    # run hbd with profile as argument
    if not dry_run:
        subprocess.call([HBD, '-b', 'chromium', '-p', profile, '-f', 'json', '--dir', profile_name], stdout=FNULL, stderr=FNULL)

    browser = 'Incogniton'
    add_profile_info(browser, profile_name, acc_info)
    
    if not dump_mode:
        # parse chromium_history.json file
        history_file = os.path.join(os.getcwd(), profile_name, 'chromium_history.json')
        parse_history_file(history_file, browser, profile_name, acc_info)

if dump_mode:
    sys.exit(0)

# sort results by visit time
results.sort(key=lambda x: x['visit_time'])

# write js
js_name = os.path.join(BASEDIR, 'data.js')
with open(js_name, mode='w') as f:
    f.write("var delta=%d,data=" % delta);
    json.dump(results, f)
    f.write(",profiles=");
    json.dump(profile_data, f)

print("Total %d histories found." % len(results))
# print(results_by_domain)

# open result page
HOMEPAGE = os.path.join(BASEDIR, 'results.html')
if sys.platform == 'darwin':
    subprocess.call(['open', HOMEPAGE], stdout=FNULL, stderr=FNULL)
if sys.platform == 'linux':
    subprocess.call(['google-chrome', HOMEPAGE], stdout=FNULL, stderr=FNULL)
elif sys.platform == 'win32':
    subprocess.call(['cmd', '/c', 'start', HOMEPAGE], stdout=FNULL, stderr=FNULL)
