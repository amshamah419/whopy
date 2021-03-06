import json
import os
import re
import socket
import sys
from codecs import encode, decode

from . import shared

dir_path = os.path.dirname(os.path.realpath(__file__))

tlds = None

dble_ext_str = "chirurgiens-dentistes.fr,in-addr.arpa,uk.net,za.org,mod.uk,org.za,za.com,de.com,us.com,hk.org,co.ca," \
               "avocat.fr,com.uy,gr.com,e164.arpa,hu.net,us.org,com.se,aeroport.fr,gov.uk,ru.com,alt.za,africa.com," \
               "geometre-expert.fr,in.net,co.com,kr.com,bl.uk,uk.com,port.fr,police.uk,gov.za,eu.com,eu.org,br.com," \
               "web.za,net.za,co.za,hk.com,ae.org,edu.ru,ar.com,jet.uk,icnet.uk,com.de,inc.hk,ltd.hk,parliament.uk," \
               "jp.net,gb.com,veterinaire.fr,edu.cn,qc.com,pharmacien.fr,ac.za,sa.com,medecin.fr,uy.com,se.net,co.pl," \
               "cn.com,hu.com,no.com,ac.uk,jpn.com,priv.at,za.net,nls.uk,nhs.uk,za.bz,experts-comptables.fr," \
               "chambagri.fr,gb.net,in.ua,notaires.fr,se.com,british-library.uk "
dble_ext = dble_ext_str.split(",")

with open(os.path.join(dir_path, "tld.json")) as fp:
    tlds = json.load(fp)


def get_whois_raw(domain, server="", previous=None, rfc3490=True, never_cut=False, with_server_list=False,
                  server_list=None):
    previous = previous or []
    server_list = server_list or []
    # Sometimes IANA simply won't give us the right root WHOIS server
    exceptions = {
        ".ac.uk": "whois.ja.net",
        ".ps": "whois.pnina.ps",
        ".buzz": "whois.nic.buzz",
        ".moe": "whois.nic.moe",
        # The following is a bit hacky, but IANA won't return the right answer for example.com because it's a direct
        # registration.
        "example.com": "whois.verisign-grs.com"
    }

    if rfc3490:
        if sys.version_info < (3, 0):
            domain = encode(domain if type(domain) is unicode else decode(domain, "utf8"), "idna")
        else:
            domain = encode(domain, "idna").decode("ascii")

    if len(previous) == 0 and server == "":
        # Root query
        is_exception = False
        for exception, exc_serv in exceptions.items():
            if domain.endswith(exception):
                is_exception = True
                target_server = exc_serv
                break
        if not is_exception:
            target_server = get_root_server(domain)
    else:
        target_server = server
    if target_server == "whois.jprs.jp":
        request_domain = "%s/e" % domain  # Suppress Japanese output
    elif domain.endswith(".de") and (target_server == "whois.denic.de" or target_server == "de.whois-servers.net"):
        request_domain = "-T dn,ace %s" % domain  # regional specific stuff
    elif target_server == "whois.verisign-grs.com":
        request_domain = "=%s" % domain  # Avoid partial matches
    else:
        request_domain = domain
    response = whois_request(request_domain, target_server)
    if never_cut:
        # If the caller has requested to 'never cut' responses, he will get the original response from the server (
        # this is useful for callers that are only interested in the raw data). Otherwise, if the target is
        # verisign-grs, we will select the data relevant to the requested domain, and discard the rest, so that in a
        # multiple-option response the parsing code will only touch the information relevant to the requested domain.
        # The side-effect of this is that when `never_cut` is set to False, any verisign-grs responses in the raw data
        # will be missing header, footer, and alternative domain options (this is handled a few lines below,
        # after the verisign-grs processing).
        new_list = [response] + previous
    if target_server == "whois.verisign-grs.com":
        # VeriSign is a little... special. As it may return multiple full records and there's no way to do an exact query,
        # we need to actually find the correct record in the list.
        for record in response.split("\n\n"):
            if re.search("Domain Name: %s\n" % domain.upper(), record):
                response = record
                break
    if never_cut == False:
        new_list = [response] + previous
    server_list.append(target_server)
    for line in [x.strip() for x in response.splitlines()]:
        match = re.match("(refer|whois server|referral url|registrar whois(?: server)?):\s*([^\s]+\.[^\s]+)", line,
                         re.IGNORECASE)
        if match is not None:
            referal_server = match.group(2)
            if referal_server != server and "://" not in referal_server:  # We want to ignore anything non-WHOIS (eg. HTTP) for now.
                # Referal to another WHOIS server...
                return get_whois_raw(domain, referal_server, new_list, server_list=server_list,
                                     with_server_list=with_server_list)
    if with_server_list:
        return new_list, server_list
    else:
        return new_list


def get_root_server(domain):
    ext = domain.split(".")[-1]
    for dble in dble_ext:
        if domain.endswith(dble):
            ext = dble

    if ext in tlds.keys():
        entry = tlds[ext]
        return entry["host"]
    else:
        raise shared.WhoisException("No root WHOIS server found for domain.")


def whois_request(domain, server, port=43):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server, port))
    sock.send(("%s\r\n" % domain).encode("utf-8"))
    buff = b""
    while True:
        data = sock.recv(1024)
        if len(data) == 0:
            break
        buff += data
    sock.close()
    try:
        d = buff.decode("utf-8")
    except UnicodeDecodeError:
        d = buff.decode("latin-1")

    return d


if __name__ == "__main__":
    d = get_whois_raw("orange.cm")
    print(d)
