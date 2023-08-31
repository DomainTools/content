import demistomock as demisto
from CommonServerPython import *
from CommonServerUserPython import *

''' IMPORTS '''
import requests
import urllib3
import dateparser
import statistics
from datetime import datetime
from typing import Dict, Any
from domaintools import API
from domaintools import utils
import urllib.parse

# disable insecure warnings
urllib3.disable_warnings()

''' GLOBALS '''

BASE_URL = demisto.params().get('base_url')
if not BASE_URL:
    BASE_URL = 'http://api.domaintools.com'  # we keep old http url for backwards comp
USERNAME = demisto.params().get('username')
API_KEY = demisto.params().get('apikey')
RISK_THRESHOLD = int(demisto.params().get('risk_threshold'))
YOUNG_DOMAIN_TIMEFRAME = int(demisto.params().get('young_domain_timeframe'))
VERIFY_CERT = not demisto.params().get('insecure', False)
PROXIES = handle_proxy()
GUIDED_PIVOT_THRESHOLD = int(demisto.params().get('pivot_threshold'))
IRIS_LINK = 'https://iris.domaintools.com/investigate/search/'

''' HELPER FUNCTIONS '''


def http_request(method, params=None):
    """
    HTTP request helper function
    Args:
        method: HTTP Method
        path: part of the url
        other_params: Anything else that needs to be in the request

    Returns: request result

    """
    api = API(
        USERNAME,
        API_KEY,
        app_partner='cortex_xsoar',
        app_name='iris-plugin',
        app_version='1',
        proxy_url=PROXIES,
        verify_ssl=VERIFY_CERT
    )

    try:
        if method == 'iris-investigate':
            response = api.iris_investigate(params.get('domains')).response()
        elif method == 'iris-enrich':
            response = api.iris_enrich(params.get('domains')).response()
        elif method == 'whois-history':
            response = api.whois_history(params.get('domain'), **params).response()
        elif method == 'hosting-history':
            response = api.hosting_history(params.get('domain')).response()
        elif method == 'reverse-whois':
            response = api.reverse_whois(**params).response()
        elif method == 'domain-profile':
            response = api.domain_profile(params.get('domain')).response()
        elif method == 'parsed-whois':
            response = api.parsed_whois(params.get('domain')).response()
        else:
            response = api.iris_investigate(**params).response()
    except Exception as e:
        message = e.reason if hasattr(e, 'reason') else e.message
        error_message = f"error for request: {params} status code: {e.code} reason: {message}"
        demisto.error(error_message)
        raise

    return response


def get_dbot_score(proximity_score, age, threat_profile_score):
    """
    Gets the DBot score
    Args:
        proximity_score: The proximity threat score deals with closeness to other malicious domains.
        age: The age of the domain.
        threat_profile_score: The threat profile score looking at things like phishing and spam.

    Returns: DBot Score

    """
    if proximity_score >= RISK_THRESHOLD or threat_profile_score >= RISK_THRESHOLD:
        return 3
    elif age < YOUNG_DOMAIN_TIMEFRAME and (proximity_score < RISK_THRESHOLD or threat_profile_score < RISK_THRESHOLD):
        return 2
    else:
        return 1

def should_include_context(include_context):
    if include_context is False:
        return False

    return include_context is not None and include_context.lower() not in [
        'false',
        '0',
    ]

def prune_context_data(data_obj):
    """
    Does a deep dive through a data object to prune any null or empty items. Checks for empty lists, dicts, and strs.
    Args:
        data_obj: Either a list or dict that needs to be pruned
    """
    items_to_prune = []
    if isinstance(data_obj, dict) and len(data_obj):
        for k, v in data_obj.items():
            if isinstance(data_obj[k], dict) or isinstance(data_obj[k], list):
                prune_context_data(data_obj[k])
            if not isinstance(v, int) and not v:
                items_to_prune.append(k)
            elif k == 'count' and v == 0:
                items_to_prune.append(k)
        for k in items_to_prune:
            del data_obj[k]
    elif isinstance(data_obj, list) and len(data_obj):
        for index, item in enumerate(data_obj):
            prune_context_data(item)
            if not isinstance(item, int) and not item:
                items_to_prune.append(index)
        data_obj[:] = [item for index, item in enumerate(data_obj) if index not in items_to_prune and len(item)]

def format_contact_grid(title, contact_dict):
    name = contact_dict.get('Name', {}).get('value')
    org = contact_dict.get('Org', {}).get('value')
    email = ','.join([email.get('value') for email in contact_dict.get('Email', {})])
    phone = contact_dict.get('Phone', {}).get('value')
    fax = contact_dict.get('Fax', {}).get('value')
    address = f"Street: {contact_dict.get('Street', {}).get('value')}, City: {contact_dict.get('City', {}).get('value')}, State: {contact_dict.get('State', {}).get('value')}, Postal: {contact_dict.get('Postal', {}).get('value')}, Country: {contact_dict.get('Country', {}).get('value')}"

    formatted_contact = [
        {'key': f'{title} Name', 'value': name} if name else None,
        {'key': f'{title} Organization', 'value': org} if org else None,
        {'key': f'{title} Email', 'value': email} if email else None,
        {'key': f'{title} Phone', 'value': phone} if phone else None,
        {'key': f'{title} Fax', 'value': fax} if fax else None,
        {'key': f'{title} Address', 'value': address},
    ]

    return [item for item in formatted_contact if item]

def format_dns_grid(type, dns_dict):
    return [{
    "type": type,
    "ip": ','.join([ip.get('value') for ip in item.get('ip')]),
    "host": item.get('host', {}).get('value')
  } for item in dns_dict]


def format_risk_grid(domain_risk):
    result = [{
        'threatcategory': 'risk_score',
        'threatcategoryconfidence': domain_risk.get('risk_score')
    }]

    for component in domain_risk.get('components', []):
        result.append({
            'threatcategory': component.get('name'),
            'threatcategoryconfidence': component.get('risk_score')
        })

    return result

def format_tags(tags):
    return ' '.join([tag.get('label') for tag in tags])

def create_domain_context_outputs(domain_result):
    """
    Creates all the context data necessary given a domain result
    Args:
        domain_result: DomainTools domain data

    Returns: Dict with context data

    """
    domain = f"{domain_result.get('domain')}"
    ip_addresses = domain_result.get('ip')
    create_date = domain_result.get('create_date', {}).get('value')
    expiration_date = domain_result.get('expiration_date', {}).get('value')
    name_servers = domain_result.get('name_server')
    domain_status = domain_result.get('active')

    proximity_risk_score = 0
    threat_profile_risk_score = 0
    threat_profile_threats = ''
    threat_profile_evidence = ''

    overall_risk_score = domain_result.get('domain_risk', {}).get('risk_score')
    risk_components = domain_result.get('domain_risk', {}).get('components')
    if risk_components:
        proximity_data = utils.get_threat_component(risk_components, 'proximity')
        blacklist_data = utils.get_threat_component(risk_components, 'blacklist')
        if proximity_data:
            proximity_risk_score = proximity_data.get('risk_score')
        elif blacklist_data:
            proximity_risk_score = blacklist_data.get('risk_score')
        threat_profile_data = utils.get_threat_component(risk_components, 'threat_profile')
        if threat_profile_data:
            threat_profile_risk_score = threat_profile_data.get('risk_score')
            threat_profile_threats = threat_profile_data.get('threats')
            threat_profile_evidence = threat_profile_data.get('evidence')

    website_response = domain_result.get('website_response')
    google_adsense = domain_result.get('adsense', {}).get('value')
    google_analytics = domain_result.get('google_analytics', {}).get('value')
    popularity_rank = domain_result.get('popularity_rank')
    tags = domain_result.get('tags')

    registrant_name = domain_result.get('registrant_name', {}).get('value')
    registrant_org = domain_result.get('registrant_org', {}).get('value')
    contact_options = ['registrant_contact', 'admin_contact', 'technical_contact', 'billing_contact']
    contact_dict = {}
    for option in contact_options:
        contact_data = domain_result.get(option, {})
        contact_dict[option] = {
            'Country': contact_data.get('country'),
            'Email': contact_data.get('email'),
            'Name': contact_data.get('name'),
            'Phone': contact_data.get('phone'),
            'Street': contact_data.get('street'),
            'City': contact_data.get('city'),
            'State': contact_data.get('state'),
            'Postal': contact_data.get('postal'),
        }
    soa_email = [soa_email.get('value') for soa_email in domain_result.get('soa_email')]
    ssl_email = [ssl_email.get('value') for ssl_email in domain_result.get('ssl_email')]
    email_domains = [email_domain.get('value') for email_domain in domain_result.get('email_domain')]
    additional_whois_emails = domain_result.get('additional_whois_email')
    domain_registrar = domain_result.get('registrar', {}).get('value') if domain_result.get('registrar') else ""
    registrar_status = domain_result.get('registrar_status')
    ip_country_code = ip_addresses[0].get('country_code', {}).get('value') if len(ip_addresses) else ''
    mx_servers = domain_result.get('mx')
    spf_info = domain_result.get('spf_info')
    ssl_certificates = domain_result.get('ssl_info')
    redirects_to = domain_result.get('redirect')
    redirect_domain = domain_result.get('redirect_domain')
    website_title = domain_result.get('website_title', {}).get('value') if domain_result.get('website_title') else ''
    server_type = domain_result.get('server_type', {}).get('value') if domain_result.get('server_type') else ''
    first_seen = domain_result.get('first_seen', {}).get('value') if domain_result.get('first_seen') else ''

    domain_tools_context = {
        'Name': domain,
        'LastEnriched': datetime.now().strftime('%Y-%m-%d'),
        'Analytics': {
            'OverallRiskScore': overall_risk_score,
            'ProximityRiskScore': proximity_risk_score,
            'ThreatProfileRiskScore': {'RiskScore': threat_profile_risk_score,
                                       'Threats': threat_profile_threats,
                                       'Evidence': threat_profile_evidence},
            'WebsiteResponseCode': website_response,
            'GoogleAdsenseTrackingCode': google_adsense,
            'GoogleAnalyticTrackingCode': google_analytics,
            'Tags': tags
        },
        'Identity': {
            'RegistrantName': registrant_name,
            'RegistrantOrg': registrant_org,
            'RegistrantContact': contact_dict.get('registrant_contact'),
            'Registrar': domain_registrar,
            'SOAEmail': soa_email,
            'SSLCertificateEmail': ssl_email,
            'AdminContact': contact_dict.get('admin_contact'),
            'TechnicalContact': contact_dict.get('technical_contact'),
            'BillingContact': contact_dict.get('billing_contact'),
            'EmailDomains': email_domains,
            'AdditionalWhoisEmails': additional_whois_emails
        },
        'Registration': {
            'RegistrarStatus': registrar_status,
            'DomainStatus': domain_status,
            'CreateDate': create_date,
            'ExpirationDate': expiration_date
        },
        'Hosting': {
            'IPAddresses': ip_addresses,
            'IPCountryCode': ip_country_code,
            'MailServers': mx_servers,
            'SPFRecord': spf_info,
            'NameServers': name_servers,
            'SSLCertificate': ssl_certificates,
            'RedirectsTo': redirects_to,
            'RedirectDomain': redirect_domain
        },
        'WebsiteTitle': website_title,
        'FirstSeen': first_seen,
        'ServerType': server_type,
    }

    domain_context = {
        'Name': domain,
        'CreationDate': create_date,
        'DomainStatus': domain_status,
        'ExpirationDate': expiration_date,
        'DNS':  [{"type": 'DNS', "ip": ip.get('address').get('value')} for ip in ip_addresses]
            + format_dns_grid('MX', mx_servers)
            + format_dns_grid('NS', name_servers),
        'Registrant': {
            'Name': registrant_name ,
            'Organization': registrant_org,
        },
        'Geo': {
            'Country': ' '.join([ip.get('country_code').get('value') for ip in ip_addresses])
        },
        'WHOIS': format_contact_grid('Admin', contact_dict.get('admin_contact', {}))
            + format_contact_grid('Registrant', contact_dict.get('registrant_contact', {}))
            + format_contact_grid('Billing', contact_dict.get('billing_contact', {}))
            + format_contact_grid('Technical', contact_dict.get('technical_contact', {}))
            + [{'key': 'Registrar', 'value': domain_registrar}],
        'Rank': [
            {
                "source": "DomainTools Popularity Rank",
                "rank": popularity_rank if popularity_rank else 'None'
            }],
        'ThreatTypes': format_risk_grid(domain_result.get('domain_risk', {})),
        'Tags': format_tags(tags)
    }

    dbot_score = 0
    if create_date != '':
        domain_age = utils.get_domain_age(create_date)
        dbot_score = get_dbot_score(proximity_risk_score, domain_age, threat_profile_risk_score)
    dbot_context = {'Indicator': domain,
                    'Type': 'domain',
                    'Vendor': 'DomainTools Iris',
                    'Score': dbot_score,
                    'Reliability': demisto.params().get('integrationReliability')}
    if dbot_score == 3:
        domain_context['Malicious'] = {
            'Vendor': 'DomainTools Iris',
            'Description': threat_profile_evidence if threat_profile_evidence is not None and len(
                threat_profile_evidence) else 'This domain has been profiled as a threat.'
        }
    outputs = {'domain': domain_context,
               'domaintools': domain_tools_context,
               'dbotscore': dbot_context}
    return outputs


def domain_investigate(domain):
    """
    Profiles domain and gives back all relevant domain data
    Args:
        domain (str): Domain name to profile

    Returns: All data relevant for Cortex XSOAR command.

    """
    return http_request('iris-investigate', {'domains': domain})

def domain_enrich(domain):
    """
    Profiles domain and gives back all relevant domain data
    Args:
        domain (str): Domain name to profile

    Returns: All data relevant for Cortex XSOAR command.

    """
    return http_request('iris-enrich', {'domains': domain})


def domain_pivot(search_params):
    """
    Analytics profile of a domain.
    Args:
        domain (str): Domain name to get analytics for

    Returns: All data relevant for Cortex XSOAR command.

    """
    return http_request('iris-pivot', search_params)

def whois_history(**kwargs):
    return http_request('whois-history', kwargs)

def hosting_history(domain):
    return http_request('hosting-history', {'domain': domain})

def reverse_whois(**kwargs):
    return http_request('reverse-whois', kwargs)

def domain_profile(domain):
    return http_request('domain-profile', {'domain': domain})

def parsed_whois(domain):
    return http_request('parsed-whois', {'domain': domain})

def profile_headers():
    return [
            'Name',
            'Last Enriched',
            'Overall Risk Score',
            'Proximity Risk Score',
            'Threat Profile Risk Score',
            'Threat Profile Threats',
            'Threat Profile Evidence',
            'Website Response Code',
            'Tags',
            'Registrant Name',
            'Registrant Org',
            'Registrant Contact',
            'Registrar',
            'SOA Email',
            'SSL Certificate Email',
            'Admin Contact',
            'Technical Contact',
            'Billing Contact',
            'Email Domains',
            'Additional Whois Emails',
            'Domain Registrant',
            'Registrar Status',
            'Domain Status',
            'Create Date',
            'Expiration Date',
            'IP Addresses',
            'IP Country Code',
            'Mail Servers',
            'SPF Record',
            'Name Servers',
            'SSL Certificate',
            'Redirects To',
            'Redirect Domain',
            'Google Adsense Tracking Code',
            'Google Analytic Tracking Code',
            'Website Title',
            'First Seen',
            'Server Type',
            'Popularity'
        ]

def add_key_to_json(cur, to_add):
    if not cur:
        return to_add
    if not isinstance(cur, list):
        return [cur, to_add]
    cur.append(to_add)
    return cur

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def format_enrich_output(result):
    domain = result.get('domain')
    context = create_domain_context_outputs(result)

    domaintools_analytics_data = context.get('domaintools', {}).get('Analytics', {})
    domaintools_hosting_data = context.get('domaintools', {}).get('Hosting', {})
    domaintools_identity_data = context.get('domaintools', {}).get('Identity', {})
    domaintools_registration_data = context.get('domaintools', {}).get('Registration', {})

    human_readable_data = {
        'Name': f"{domain}",
        'Last Enriched': datetime.now().strftime('%Y-%m-%d'),
        'Overall Risk Score': domaintools_analytics_data.get('OverallRiskScore', ''),
        'Proximity Risk Score': domaintools_analytics_data.get('ProximityRiskScore', ''),
        'Threat Profile Risk Score': domaintools_analytics_data.get('ThreatProfileRiskScore', {}).get('RiskScore',
                                                                                                      ''),
        'Threat Profile Threats': domaintools_analytics_data.get('ThreatProfileRiskScore', {}).get('Threats', ''),
        'Threat Profile Evidence': domaintools_analytics_data.get('ThreatProfileRiskScore', {}).get('Evidence', ''),
        'Google Adsense Tracking Code': domaintools_analytics_data.get('GoogleAdsenseTrackingCode', ''),
        'Google Analytic Tracking Code': domaintools_analytics_data.get('GoogleAnalyticTrackingCode', ''),
        'Website Response Code': domaintools_analytics_data.get('WebsiteResponseCode', ''),
        'Tags': domaintools_analytics_data.get('Tags', ''),
        'Registrant Name': domaintools_identity_data.get('RegistrantName', ''),
        'Registrant Org': domaintools_identity_data.get('RegistrantOrg', ''),
        'Registrant Contact': domaintools_identity_data.get('RegistrantContact', ''),
        'Registrar': domaintools_identity_data.get('Registrar', ''),
        'SOA Email': domaintools_identity_data.get('SOAEmail', ''),
        'SSL Certificate Email': domaintools_identity_data.get('SSLCertificateEmail', ''),
        'Admin Contact': domaintools_identity_data.get('AdminContact', ''),
        'Technical Contact': domaintools_identity_data.get('TechnicalContact', ''),
        'Billing Contact': domaintools_identity_data.get('BillingContact', ''),
        'Email Domains': domaintools_identity_data.get('EmailDomains', ''),
        'Additional Whois Emails': domaintools_identity_data.get('AdditionalWhoisEmails', ''),
        'Registrar Status': domaintools_registration_data.get('RegistrarStatus', ''),
        'Domain Status': domaintools_registration_data.get('DomainStatus', ''),
        'Create Date': domaintools_registration_data.get('CreateDate', ''),
        'Expiration Date': domaintools_registration_data.get('ExpirationDate', ''),
        'IP Addresses': domaintools_hosting_data.get('IPAddresses', ''),
        'IP Country Code': domaintools_hosting_data.get('IPCountryCode', ''),
        'Mail Servers': domaintools_hosting_data.get('MailServers', ''),
        'SPF Record': domaintools_hosting_data.get('SPFRecord', ''),
        'Name Servers': domaintools_hosting_data.get('NameServers', ''),
        'SSL Certificate': domaintools_hosting_data.get('SSLCertificate', ''),
        'Redirects To': domaintools_hosting_data.get('RedirectsTo', ''),
        'Redirect Domain': domaintools_hosting_data.get('RedirectDomain', ''),
        'Website Title': context.get('domaintools', {}).get('WebsiteTitle'),
        'First Seen': context.get('domaintools', {}).get('FirstSeen'),
        'Server Type': context.get('domaintools', {}).get('ServerType'),
        'Popularity': context.get('domain', {}).get('Rank'),
    }

    demisto_title = f'DomainTools Iris Enrich for {domain}.'
    iris_title = 'Investigate [{0}](https://research.domaintools.com/iris/search/?q={0}) in Iris.'.format(domain)
    headers = profile_headers()
    human_readable = tableToMarkdown(
        f'{demisto_title} {iris_title}', human_readable_data, headers=headers
    )

    return (human_readable, context)

def format_ips(ips):
    for ip in ips:
        address = ip['address']
        address['count'] = format_guided_pivot_link("ip.ip", address)

        asns = ip['asn']
        for asn in asns:
            asn['count'] = format_guided_pivot_link("ip.asn", asn)

        country_code = ip['country_code']
        country_code['count'] = format_guided_pivot_link("ip.cc", country_code)

        isp = ip['isp']
        isp['count'] = format_guided_pivot_link("ip.isp", isp)

    return ips

def format_nameserver(nameservers):
    for ns in nameservers:
        host = ns['host']
        host['count'] = format_guided_pivot_link("ns.ns", host)

        ips = ns['ip']
        for ip in ips:
            ip['count'] = format_guided_pivot_link("ns.nip", ip)

        domain = ns['domain']
        domain['count'] = format_guided_pivot_link("ns.nsd", domain)

    return nameservers



def format_mailserver(mailservers):
    for mx in mailservers:
        host = mx['host']
        host['count'] = format_guided_pivot_link("mx.mx", host)

        ips = mx['ip']
        for ip in ips:
            ip['count'] = format_guided_pivot_link("mx.mip", ip)

        domain = mx['domain']
        domain['count'] = format_guided_pivot_link("mx.mxd", domain)

    return mailservers


def format_ssl_info(certs):
    for cert in certs:
        alt_names = cert['alt_names']
        for an in alt_names:
            an['count'] = format_guided_pivot_link("ssl.alt_names", an)

        ssl_hash = cert['hash']
        ssl_hash['count'] = format_guided_pivot_link("ssl.sh", ssl_hash)

        subject = cert['subject']
        subject['count'] = format_guided_pivot_link("ssl.s", subject)

        org = cert['organization']
        org['count'] = format_guided_pivot_link("ssl.so", org)

        cn = cert['common_name']
        cn['count'] = format_guided_pivot_link("ssl.common_name", cn)

        icn = cert['issuer_common_name']
        icn['count'] = format_guided_pivot_link("ssl.issuer_common_name", icn)

        na = cert['not_after']
        na['count'] = format_guided_pivot_link("ssl.not_after", na)

        nb = cert['not_before']
        nb['count'] = format_guided_pivot_link("ssl.not_before", nb)

        duration = cert['duration']
        duration['count'] = format_guided_pivot_link("ssl.duration", duration)

    return certs

def format_contact(contact, domain, email_type):
    country = contact['country']
    country['count'] = format_guided_pivot_link('cons.cc', country)
    name = contact['name']
    name['count'] = format_guided_pivot_link('cons.nm', name)
    phone = contact['phone']
    phone['count'] = format_guided_pivot_link('cons.ph', phone)
    street = contact['street']
    street['count'] = format_guided_pivot_link('cons.str', street)

    org = contact['org']
    org['count'] = format_guided_pivot_link(None, org, domain)
    city = contact['city']
    city['count'] = format_guided_pivot_link(None, city, domain)
    state = contact['state']
    state['count'] = format_guided_pivot_link(None, state, domain)
    postal = contact['postal']
    postal['count'] = format_guided_pivot_link(None, postal, domain)
    fax = contact['fax']
    fax['count'] = format_guided_pivot_link(None, fax, domain)

    emails = contact['email']
    for email in emails:
        email['count'] = format_guided_pivot_link(email_type, email)

    return contact


def format_single_value(link_type, value, domain = None):
    if isinstance(value, str):
        return value

    value['count'] = format_guided_pivot_link(link_type, value, domain)

    return json.dumps(value, ensure_ascii=False)


def format_list_value(link_type, list, domain=None):
    for item in list:
        item['count'] = format_guided_pivot_link(link_type, item, domain)

    return list

def format_guided_pivot_link(link_type, item, domain=None):
    query = item.get('value')
    count = item.get('count')

    if domain:
        link_type ='domain'
        query = domain

    if 1 < int(count) < GUIDED_PIVOT_THRESHOLD:
        return f'[{count}]({IRIS_LINK}?q={link_type}:"{urllib.parse.quote(str(query), safe="")}")'

    return count


def format_investigate_output(result):
    domain = result.get('domain')
    context = create_domain_context_outputs(result)

    domaintools_analytics_data = context.get('domaintools', {}).get('Analytics', {})
    domaintools_hosting_data = context.get('domaintools', {}).get('Hosting', {})
    domaintools_registration_data = context.get('domaintools', {}).get('Registration', {})

    human_readable_data = {
        'Name': f"[{domain}](https://domaintools.com)",
        'Last Enriched': datetime.now().strftime('%Y-%m-%d'),
        'Overall Risk Score': domaintools_analytics_data.get('OverallRiskScore', ''),
        'Proximity Risk Score': domaintools_analytics_data.get('ProximityRiskScore', ''),
        'Threat Profile Risk Score': domaintools_analytics_data.get('ThreatProfileRiskScore', {}).get('RiskScore',
                                                                                                      ''),
        'Threat Profile Threats': domaintools_analytics_data.get('ThreatProfileRiskScore', {}).get('Threats', ''),
        'Threat Profile Evidence': domaintools_analytics_data.get('ThreatProfileRiskScore', {}).get('Evidence', ''),
        'Google Adsense Tracking Code': format_single_value('ad', result.get('adsense', {})),
        'Google Analytic Tracking Code': format_single_value('ga', result.get('google_analytics', {})),
        'Website Response Code': domaintools_analytics_data.get('WebsiteResponseCode', ''),
        'Tags': domaintools_analytics_data.get('Tags', 'not here'),
        'Registrant Name': format_single_value('r_n', result.get('registrant_name', {})),
        'Registrant Org': format_single_value('r_o', result.get('registrant_org', {})),
        'Registrant Contact': format_contact(result.get('registrant_contact', {}), domain, 'empr'),
        'Registrar': format_single_value('reg', result.get('registrar', {})),
        'SOA Email': format_list_value('ema', result.get('soa_email', [])),
        'SSL Certificate Email': format_list_value('ssl.em', result.get('ssl_email', [])),
        'Admin Contact': format_contact(result.get('admin_contact', {}), domain, 'empa'),
        'Technical Contact': format_contact(result.get('technical_contact', {}), domain, 'empt'),
        'Billing Contact': format_contact(result.get('billing_contact', {}), domain, 'empb'),
        'Email Domains': format_list_value('emd', result.get('email_domain', [])),
        'Additional Whois Emails': format_list_value('em', result.get('additional_whois_email', [])),
        'Registrar Status': domaintools_registration_data.get('RegistrarStatus', ''),
        'Domain Status': domaintools_registration_data.get('DomainStatus', ''),
        'Create Date': format_single_value('cre', result.get('create_date', {})),
        'Expiration Date': format_single_value('exp', result.get('expiration_date', {})),
        'IP Addresses': format_ips(result.get('ip', {})),
        'IP Country Code': domaintools_hosting_data.get('IPCountryCode', ''),
        'Mail Servers': format_mailserver(result.get('mx', {})),
        'SPF Record': format_single_value(None, result.get('spf_info', {}), domain),
        'Name Servers': format_nameserver(result.get('name_server', {})),
        'SSL Certificate': format_ssl_info(result.get('ssl_info', {})),
        'Redirects To': format_single_value(None, result.get('redirect', {}), domain),
        'Redirect Domain': format_single_value('rdd', result.get('redirect_domain', {})),
        'Website Title': format_single_value(None, result.get('website_title', {}), domain),
        'First Seen': format_single_value(None, result.get('first_seen', {}), domain),
        'Server Type': format_single_value('server_type', result.get('server_type', {})),
        'Popularity': result.get('popularity_rank'),
    }

    demisto_title = f'DomainTools Iris Investigate for {domain}.'
    iris_title = 'Investigate [{0}](https://research.domaintools.com/iris/search/?q={0}) in Iris.'.format(domain)
    headers = profile_headers()
    human_readable = tableToMarkdown(
        f'{demisto_title} {iris_title}', human_readable_data, headers=headers
    )

    return (human_readable, context)
''' COMMANDS '''


def domain_command():
    """
    Command to do a total profile of a domain.
    """
    domain = demisto.args().get('domain')
    domain_list = domain.split(",")
    domain_chunks = chunks(domain_list, 100)
    include_context = demisto.args().get('include_context', False)

    all_human_readable_output = ''
    all_raw_response = []
    all_context = {'Domain': [], 'DomainTools': [], "DBotScore": []}
    all_missing_domains = []

    for chunk in domain_chunks:
        response = domain_investigate(','.join(chunk))
        all_raw_response.append(response)
        all_missing_domains += response.get("missing_domains")
        for result in response.get('results', []):
            human_readable_output, context = format_investigate_output(result)
            all_human_readable_output += human_readable_output

            if should_include_context(include_context):
                all_context['Domain'].append(context.get('domain'))
                all_context['DomainTools'].append(context.get('domaintools'))
                all_context['DBotScore'].append(context.get('dbotscore'))

    if len(all_missing_domains) > 0:
        all_human_readable_output += f"Missing Domains: {','.join(all_missing_domains)}"

    if not should_include_context(include_context):
        all_context = None

    results = CommandResults(
        outputs_prefix='',
        outputs_key_field='Name',
        outputs=all_context,
        readable_output=all_human_readable_output,
        ignore_auto_extract=True,
        raw_response=all_raw_response
    )
    return_results(results)


def domain_enrich_command():
    """
    Command to do a total profile of a domain.
    """
    domain = demisto.args().get('domain')
    domain_list = domain.split(",")
    domain_chunks = chunks(domain_list, 100)
    include_context = demisto.args().get('include_context', False)

    all_human_readable_output = ''
    all_raw_response = []
    all_context = {'Domain': [], 'DomainTools': [], "DBotScore": []}
    all_missing_domains = []

    for chunk in domain_chunks:
        response = domain_enrich(','.join(chunk))
        all_raw_response.append(response)
        all_missing_domains += response.get("missing_domains")
        for result in response.get('results', []):
            human_readable_output, context = format_enrich_output(result)
            all_human_readable_output += human_readable_output

            if should_include_context(include_context):
                all_context['Domain'].append(context.get('domain'))
                all_context['DomainTools'].append(context.get('domaintools'))
                all_context['DBotScore'].append(context.get('dbotscore'))

    if len(all_missing_domains) > 0:
        all_human_readable_output += f"Missing Domains: {','.join(all_missing_domains)}"

    if not should_include_context(include_context):
        all_context = None

    results = CommandResults(
        outputs_prefix='',
        outputs_key_field='Name',
        outputs=all_context,
        readable_output=all_human_readable_output,
        ignore_auto_extract=True,
        raw_response=all_raw_response
    )
    return_results(results)


def domain_analytics_command():
    """
    Command to do a analytics profile of a domain.
    """
    domain = demisto.args().get('domain')
    response = domain_investigate(domain)
    human_readable = 'No results found.'
    outputs = {}  # type: Dict[Any, Any]

    if response.get('results_count'):
        domain_result = response.get('results')[0]
        context = create_domain_context_outputs(domain_result)
        outputs = {'Domain(val.Name && val.Name == obj.Name)': context.get('domain'),
                   'DomainTools.Domains(val.Name && val.Name == obj.Name)': context.get('domaintools'),
                   'DBotScore': context.get('dbotscore')}
        prune_context_data(outputs)
        domaintools_analytics_data = context.get('domaintools', {}).get('Analytics', {})
        domain_age = 0
        create_date = context.get('domaintools').get('Registration').get('CreateDate', '')
        if create_date != '':
            domain_age = utils.get_domain_age(create_date)
        human_readable_data = {
            'Overall Risk Score': domaintools_analytics_data.get('OverallRiskScore', ''),
            'Proximity Risk Score': domaintools_analytics_data.get('ProximityRiskScore', ''),
            'Threat Profile Risk Score': domaintools_analytics_data.get('ThreatProfileRiskScore', {}).get('RiskScore',
                                                                                                          ''),
            'Domain Age (in days)': domain_age,
            'Website Response': domaintools_analytics_data.get('WebsiteResponseCode', ''),
            'Google Adsense': domaintools_analytics_data.get('GoogleAdsenseTrackingCode', ''),
            'Google Analytics': domaintools_analytics_data.get('GoogleAnalyticsTrackingCode', ''),
            'Tags': domaintools_analytics_data.get('Tags', ''),
        }

        headers = ['Overall Risk Score',
                   'Proximity Risk Score',
                   'Domain Age (in days)',
                   'Website Response',
                   'Google Adsense',
                   'Google Analytics',
                   'Tags']
        demisto_title = 'DomainTools Domain Analytics for {}.'.format(domain)
        iris_title = 'Investigate [{0}](https://research.domaintools.com/iris/search/?q={0}) in Iris.'.format(domain)
        human_readable = tableToMarkdown('{} {}'.format(demisto_title, iris_title),
                                         human_readable_data,
                                         headers=headers)
    return_outputs(human_readable, outputs, response)


def threat_profile_command():
    """
    Command to do a threat profile of a domain.
    """
    domain = demisto.args().get('domain')
    response = domain_investigate(domain)
    human_readable = 'No results found.'
    outputs = {}  # type: Dict[Any, Any]

    if response.get('results_count'):
        domain_result = response.get('results')[0]
        context = create_domain_context_outputs(domain_result)
        outputs = {'Domain(val.Name && val.Name == obj.Name)': context.get('domain'),
                   'DomainTools.Domains(val.Name && val.Name == obj.Name)': context.get('domaintools'),
                   'DBotScore': context.get('dbotscore')}
        prune_context_data(outputs)
        proximity_risk_score = 0
        threat_profile_risk_score = 0
        threat_profile_malware_risk_score = 0
        threat_profile_phishing_risk_score = 0
        threat_profile_spam_risk_score = 0
        threat_profile_threats = ''
        threat_profile_evidence = ''

        overall_risk_score = domain_result.get('domain_risk', {}).get('risk_score', 0)
        risk_components = domain_result.get('domain_risk', {}).get('components', {})
        if risk_components:
            proximity_data = utils.get_threat_component(risk_components, 'proximity')
            blacklist_data = utils.get_threat_component(risk_components, 'blacklist')
            if proximity_data:
                proximity_risk_score = proximity_data.get('risk_score', 0)
            elif blacklist_data:
                proximity_risk_score = blacklist_data.get('risk_score', 0)
            threat_profile_data = utils.get_threat_component(risk_components, 'threat_profile')
            if threat_profile_data:
                threat_profile_risk_score = threat_profile_data.get('risk_score', 0)
                threat_profile_threats = ', '.join(threat_profile_data.get('threats', []))
                threat_profile_evidence = ', '.join(threat_profile_data.get('evidence', []))
            threat_profile_malware_data = utils.get_threat_component(risk_components, 'threat_profile_malware')
            if threat_profile_malware_data:
                threat_profile_malware_risk_score = threat_profile_malware_data.get('risk_score', 0)
            threat_profile_phshing_data = utils.get_threat_component(risk_components, 'threat_profile_phishing')
            if threat_profile_phshing_data:
                threat_profile_phishing_risk_score = threat_profile_phshing_data.get('risk_score', 0)
            threat_profile_spam_data = utils.get_threat_component(risk_components, 'threat_profile_spam')
            if threat_profile_spam_data:
                threat_profile_spam_risk_score = threat_profile_spam_data.get('risk_score', 0)

        human_readable_data = {
            'Overall Risk Score': overall_risk_score,
            'Proximity Risk Score': proximity_risk_score,
            'Threat Profile Risk Score': threat_profile_risk_score,
            'Threat Profile Threats': threat_profile_threats,
            'Threat Profile Evidence': threat_profile_evidence,
            'Threat Profile Malware Risk Score': threat_profile_malware_risk_score,
            'Threat Profile Phishing Risk Score': threat_profile_phishing_risk_score,
            'Threat Profile Spam Risk Score': threat_profile_spam_risk_score
        }

        headers = ['Overall Risk Score',
                   'Proximity Risk Score',
                   'Threat Profile Risk Score',
                   'Threat Profile Threats',
                   'Threat Profile Evidence',
                   'Threat Profile Malware Risk Score',
                   'Threat Profile Phishing Risk Score',
                   'Threat Profile Spam Risk Score']
        demisto_title = 'DomainTools Threat Profile for {}.'.format(domain)
        iris_title = 'Investigate [{0}](https://research.domaintools.com/iris/search/?q={0}) in Iris.'.format(domain)
        human_readable = tableToMarkdown('{} {}'.format(demisto_title, iris_title),
                                         human_readable_data,
                                         headers=headers)
    return_outputs(human_readable, outputs, response)


def domain_pivot_command():
    """
    Command to do a domain pivot lookup.
    """
    search_data = {}  # type: Dict[Any, Any]
    search_type = ''
    search_value = ''
    available_pivots = {
        'ip': 'IP',
        'email': 'E-Mail',
        'nameserver_ip': 'Name Server IP',
        'ssl_hash': 'SSL Hash',
        'nameserver_host': 'Name Server Host',
        'mailserver_host': 'Mail Server Host',
        'email_domain': 'Email Domain',
        'nameserver_domain': 'Name Server Domain',
        'registrar': 'Registrar',
        'registrant': 'Registrant',
        'registrant_org': 'Registrant Org',
        'tagged_with_any': 'Tagged with Any',
        'tagged_with_all': 'Tagged with All',
        'mailserver_domain': 'Mail Server Domain',
        'mailserver_ip': 'Mail Server IP',
        'redirect_domain': 'Redirect Domain',
        'ssl_org': 'SSL Org',
        'ssl_subject': 'SSL Subject',
        'ssl_email': 'SSL Email',
        'google_analytics': 'Google Analytics',
        'adsense': 'Adsense',
        'search_hash': 'Iris Search Hash'
    }
    current_date = datetime.utcnow()

    for pivot_type in available_pivots:
        if demisto.args().get(pivot_type):
            search_data = {pivot_type: demisto.args().get(pivot_type)}
            search_type, search_value = available_pivots[pivot_type], demisto.args().get(pivot_type)
            break

    if not search_type or not search_value:
        raise Exception(f"Invalid pivot type or value. pivot type: {search_type} search value: {search_value}")

    response = domain_pivot(search_data)
    results = response['results']
    while response['has_more_results']:
        search_data['position'] = response['position']
        response = domain_pivot(search_data)
        results.extend(response['results'])

    output = []
    domain_context_list = []
    risk_list = []
    age_list = []
    count = 0
    human_readable = 'No results found.'
    include_context = demisto.args().get('include_context', False)

    if response.get('results_count'):
        for domain_result in results:
            risk_score = domain_result.get('domain_risk', {}).get('risk_score')
            first_seen = domain_result.get('first_seen', {}).get('value') if domain_result.get('first_seen') else False
            output.append({'domain': domain_result.get('domain'), 'risk_score': risk_score})

            if risk_score is not None:
                risk_list.append(risk_score)
            if first_seen:
                timestamp = datetime.strptime(first_seen, "%Y-%m-%dT%H:%M:%SZ")
                age = (current_date - timestamp).days
                age_list.append(age)
            if should_include_context(include_context):
                domain_context = create_domain_context_outputs(domain_result)
                domain_context_list.append(domain_context.get('domaintools'))

            count += 1

        average_risk = round(statistics.mean(risk_list), 2) if risk_list else "Unknown"
        average_age = round(statistics.mean(age_list), 2) if age_list else "Unknown"

        outputs = {'DomainTools.PivotedDomains(val.Name == obj.Name)': domain_context_list}
        prune_context_data(outputs)
        headers = ['domain', 'risk_score']

        sorted_output = sorted(output, key=lambda x: x['risk_score'] if x['risk_score'] is not None else -1, reverse=True)
        human_readable = tableToMarkdown(f'Domains for {search_type}: {search_value} ({count} results, {average_risk} average risk, {average_age} average age)',
                                         sorted_output,
                                         headers=headers)

    results = CommandResults(
        outputs_prefix='DomainTools.PivotedDomains',
        outputs_key_field='Name',
        outputs=domain_context_list,
        readable_output=human_readable,
        ignore_auto_extract=True
    )
    return_results(results)

def to_camel_case(value):
    str = f' {value.strip()}'
    str = re.sub(r' ([a-z,A-Z])', lambda g: g.group(1).upper(), str)
    return str


def whois_history_command():
    domain = demisto.args().get('domain')
    sort = demisto.args().get('sort')
    limit = demisto.args().get('limit')
    mode = demisto.args().get('mode')
    offset = demisto.args().get('offset')
    response = whois_history(domain=domain, sort=sort, limit=limit, mode=mode, offset=offset)
    history = response.get('history', [])

    all_context = []
    human_readable = ''

    for entry in history:
        record = entry.get('whois', {}).get('record')
        split_record = record.split('\n')
        entry_context = {}
        table = {}
        headers = []

        for pair in split_record:
            split_entry = re.split(r':\s(.+)', pair)
            if len(split_entry) > 1:
                label = split_entry[0].rstrip('.')
                value = split_entry[1]

                headers.append(label)
                table[label] = value
                entry_context[to_camel_case(label)] = value

        human_readable += tableToMarkdown(f"{domain}: {entry.get('date')}", table, headers=headers)
        all_context.append(entry_context)

    all_context = {'Domain' : {'Name' : domain, 'WhoisHistory' : all_context}}

    if mode == 'count':
        human_readable = f'record count: {response.get("record_count")}'
    if mode == 'check_existence':
        human_readable = f'has history entiries: {response.get("has_history_entries")}'

    results = CommandResults(
        outputs_prefix='Domain',
        outputs_key_field='Name',
        outputs=all_context,
        readable_output=human_readable,
        ignore_auto_extract=True
    )
    return_results(results)


def create_history_table(data, headers):
    table = []
    for row in data:
        entry = {header: row.get(header) for header in headers}
        table.append(entry)

    return table

def hosting_history_command():
    domain = demisto.args().get('domain')
    response = hosting_history(domain)

    ip_history = response.get('ip_history', [])
    ip_headers = ['domain', 'actiondate', 'action', 'action_in_words', 'post_ip', 'pre_ip']
    ip_table = create_history_table(ip_history, ip_headers)
    human_readable_ip = tableToMarkdown(
        "IP Address History", ip_table, headers=ip_headers
    )

    ns_history = response.get('nameserver_history', [])
    ns_headers = ['domain', 'actiondate', 'action', 'action_in_words', 'post_mns', 'pre_mns']
    ns_table = create_history_table(ns_history, ns_headers)
    human_readable_ns = tableToMarkdown(
        "Name Server History", ns_table, headers=ns_headers
    )

    registrar_history = response.get('registrar_history', [])
    registrar_headers = ['domain', 'date_created', 'date_expires', 'date_lastchecked', 'date_updated',  'registrar', 'registrartag']
    registrar_table = create_history_table(registrar_history, registrar_headers)
    human_readable_registrar = tableToMarkdown(
        "Registrar History", registrar_table, headers=registrar_headers
    )

    human_readable_all = human_readable_registrar + human_readable_ns + human_readable_ip
    all_context = {'Name': domain, 'IPHistory': ip_table, 'NameserverHistory': ns_table, 'RegistrarHistory': registrar_table}

    results = CommandResults(
        outputs_prefix='DomainTools',
        outputs_key_field='DomainTools.Name',
        outputs=all_context,
        readable_output=human_readable_all,
        ignore_auto_extract=True
    )
    return_results(results)

def reverse_whois_command():
    terms = demisto.args().get('terms')
    exclude = demisto.args().get('exclude')
    scope = (
        'current'
        if demisto.args().get('onlyHistoricScope') == 'false'
        else 'historic'
    )
    results = reverse_whois(query=terms, mode='purchase', exclude=exclude, scope=scope)
    domains = results.get('domains', [])

    context = []
    human_readable = f'Found {len(domains)}' + ' domains: \n'

    for domain in domains:
        human_readable += f'* {domain}' + '\n'
        context.append({'Name': domain})

    all_context = {'Domain': context}
    results = CommandResults(
        outputs_prefix='Domain',
        outputs_key_field='Name',
        outputs=all_context,
        readable_output=human_readable,
        ignore_auto_extract=True
    )
    return_results(results)

def domain_profile_command():
    domain = demisto.args().get('domain')
    results = domain_profile(domain)
    return_results({'response': results})

def to_camel_case(string):
    str_with_space = ' ' + string.strip()
    str_with_space = re.sub(r' ([a-zA-Z])', lambda g: g.group(1).upper(), str_with_space)
    return str_with_space

def change_keys(conv, obj):
    output = {}
    for key, value in obj.items():
        if isinstance(value, dict):
            output[conv(key)] = change_keys(conv, value)
        else:
            output[conv(key)] = value
    return output
def parsed_whois_command():
    domain = demisto.args().get('query')
    response = parsed_whois(domain)

    whois_record = response.get('whois', {}).get('record', '')
    split_record = whois_record.split('\n')
    table = {}
    headers = []
    for entry in split_record:
        split_entry = re.split(r':\s(.+)', entry)
        if len(split_entry) > 1:
            headers.append(split_entry[0])
            table[split_entry[0]] = split_entry[1]

    human_readable = tableToMarkdown(f'DomainTools whois result for {domain}', table, headers=headers)

    context = {
        'Domain': {
            'Name': response.get('record_source'),
            'Whois': change_keys(to_camel_case, response.get('parsed_whois'))
        }
    }

    results = CommandResults(
        outputs_prefix='Domain',
        outputs_key_field='Name',
        outputs=context,
        readable_output=human_readable,
        ignore_auto_extract=True
    )
    return_results(results)

def reverse_ip_command():
    return_error('replaced by domaintoolsiris-pivot ip=')

def reverse_ns_command():
    return_error('replaced by domaintoolsiris-pivot name_server=')

def test_module():
    """
    Tests the API key for a user.
    """
    try:
        http_request('GET', '/v1/iris-investigate/', {'domain': 'demisto.com'})
        demisto.results('ok')
    except Exception:
        raise


def main():
    """
    Main Cortex XSOAR function.
    """
    try:
        if demisto.command() == 'test-module':
            test_module()
        elif demisto.command() == 'domain':
            domain_command()
        elif demisto.command() == 'domaintoolsiris-analytics':
            domain_analytics_command()
        elif demisto.command() == 'domaintoolsiris-threat-profile':
            threat_profile_command()
        elif demisto.command() == 'domaintoolsiris-pivot':
            domain_pivot_command()
        elif demisto.command() == 'domaintoolsiris-enrich':
            domain_enrich_command()
        elif demisto.command() == 'whoisHistory':
            whois_history_command()
        elif demisto.command() == 'hostingHistory':
            hosting_history_command()
        elif demisto.command() == 'reverseWhois':
            reverse_whois_command()
        elif demisto.command() == 'domainProfile':
            domain_profile_command()
        elif demisto.command() == 'whois':
            parsed_whois_command()
        elif demisto.command() == 'reverseIP':
            reverse_ip_command()
        elif demisto.command() == 'reverseNameServer':
            reverse_ns_command()
    except Exception as e:
        return_error(
            f'Unable to perform command : {demisto.command()}, Reason: {str(e)}, Stack: {traceback.format_exc()}'
        )


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
