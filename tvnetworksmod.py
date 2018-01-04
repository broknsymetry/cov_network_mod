# -*- coding: utf-8 -*-

'''
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


from resources.lib.modules import trakt
from resources.lib.modules import cleantitle
from resources.lib.modules import cleangenre
from resources.lib.modules import control
from resources.lib.modules import client
from resources.lib.modules import cache
from resources.lib.modules import metacache
from resources.lib.modules import playcount
from resources.lib.modules import workers
from resources.lib.modules import views
from resources.lib.modules import utils
from resources.lib.indexers import navigator

import os,sys,re,json,urllib,urlparse,datetime,xbmcgui


def get(self, url, idx=True, create_directory=True):
    try:
        try: url = getattr(self, url + '_link')
        except: pass

        try: u = urlparse.urlparse(url).netloc.lower()
        except: pass


        if u in self.trakt_link and '/users/' in url:
            try:
                if not '/users/me/' in url: raise Exception()
                if trakt.getActivity() > cache.timeout(self.trakt_list, url, self.trakt_user): raise Exception()
                self.list = cache.get(self.trakt_list, 720, url, self.trakt_user)
            except:
                self.list = cache.get(self.trakt_list, 0, url, self.trakt_user)

            if '/users/me/' in url and '/collection/' in url:
                self.list = sorted(self.list, key=lambda k: utils.title_key(k['title']))

            if idx == True: self.worker()

        elif u in self.trakt_link and self.search_link in url:
            self.list = cache.get(self.trakt_list, 1, url, self.trakt_user)
            if idx == True: self.worker(level=0)

        elif u in self.trakt_link:
            self.list = cache.get(self.trakt_list, 24, url, self.trakt_user)
            if idx == True: self.worker()


        elif u in self.imdb_link and ('/user/' in url or '/list/' in url):
            self.list = cache.get(self.imdb_list, 0, url)
            if idx == True: self.worker()

        elif u in self.imdb_link:
            self.list = cache.get(self.imdb_list, 24, url)
            if idx == True: self.worker()

        elif u in self.tvmaze_link and '?Network' in url:
            self.list = cache.get(self.countries, 168, url)
            if idx == True: self.getNetworks(url)

        elif u in self.tvmaze_link:
            self.list = cache.get(self.tvmaze_list, 0, url)#168
            if idx == True: self.worker()


        if idx == True and create_directory == True: self.tvshowDirectory(self.list)
        return self.list
    except:
        pass

def countries(self):
    countries =  [('United States', '235'),
    ('United Kingdom', '234'),
    ('Afghanistan', '1'),
    ('Albania', '3'),
    ('Argentina', '11'),
    ('Armenia', '12'),
    ('Australia', '14'),
    ('Austria', '15'),
    ('Azerbaijan', '16'),
    ('Belarus', '21'),
    ('Belgium', '22'),
    ('Bosnia and Herzegovina', '29'),
    ('Brazil', '32'),
    ('Bulgaria', '35'),
    ('Canada', '40'),
    ('Chile', '45'),
    ('China', '46'),
    ('Colombia', '49'),
    ('Croatia', '56'),
    ('Cyprus', '59'),
    ('Czech Republic', '60'),
    ('Denmark', '61'),
    ('Estonia', '70'),
    ('Finland', '75'),
    ('France', '76'),
    ('French Polynesia', '78'),
    ('Georgia', '82'),
    ('Germany', '83'),
    ('Greece', '86'),
    ('Hong Kong', '100'),
    ('Hungary', '101'),
    ('Iceland', '102'),
    ('India', '103'),
    ('Indonesia', '104'),
    ('Iran', '105'),
    ('Iraq', '106'),
    ('Ireland', '107'),
    ('Israel', '109'),
    ('Italy', '110'),
    ('Japan', '112'),
    ('Kazakhstan', '115'),
    ('North Korea', '118'),
    ('South Korea', '119'),
    ('Latvia', '123'),
    ('Lebanon', '124'),
    ('Lithuania', '129'),
    ('Malaysia', '135'),
    ('Maldives', '136'),
    ('Mexico', '144'),
    ('Moldova', '146'),
    ('Netherlands', '157'),
    ('New Zealand', '159'),
    ('Norway', '166'),
    ('Pakistan', '169'),
    ('Peru', '174'),
    ('Philippines', '175'),
    ('Poland', '177'),
    ('Portugal', '178'),
    ('Puerto Rico', '179'),
    ('Qatar', '180'),
    ('Romania', '182'),
    ('Russian Federation', '183'),
    ('Saudi Arabia', '195'),
    ('Serbia', '197'),
    ('Singapore', '200'),
    ('Slovenia', '203'),
    ('South Africa', '206'),
    ('Spain', '208'),
    ('Sweden', '214'),
    ('Switzerland', '215'),
    ('Taiwan', '217'),
    ('Thailand', '220'),
    ('Turkey', '227'),
    ('Ukraine', '232'),
    ('United Arab Emirates', '233'),
    ('Venezuela', '240')]

    self.tvmaze_networks_link = 'http://www.tvmaze.com/networks?Network[country_enum]=%s&Network[sort]=3'#, 'http://www.tvmaze.com/webchannels?WebChannel[country_enum]=%s&WebChannel[sort]=3']
    for i in countries:
        self.list.append(
        {
            'name': cleangenre.lang(i[0], self.lang),
            'url': self.tvmaze_networks_link % i[1],
            'image': '',
            'action': 'tvshows'
        })

    self.addDirectory(self.list)
    return self.list

def networks(self):
    self.countries()
    return

def getNetworks(self, url):

    self.list = []

    try:
        def maxpage(url):
            maxp = client.request(url + '&page=1000')
            maxp = client.parseDOM(maxp, 'ul', attrs = {'class': 'pagination'})
            maxp = client.parseDOM(maxp, 'li', attrs = {'class': 'current'})
            maxp = client.parseDOM(maxp, 'a')

            if not maxp:
                maxpage = 1
            else:
                maxpage = int(maxp[0])
            return maxpage

        mp = maxpage(url)
        for p in range(1, mp+1):
            network_page = client.request(url + '&page=' + str(p))
            networks = client.parseDOM(network_page, 'div', attrs = {'class': 'card primary grid-x'})
            for i in networks:
                network = client.parseDOM(i, 'figure', attrs = {'class': 'image small-12 cell'})
                title = client.parseDOM(i, 'span', attrs = {'class': 'title'})
                title = client.parseDOM(title, 'a')
                title = title[0].encode('utf-8')
                u = client.parseDOM(network, 'a', ret='href')
                u = u[0].encode('utf-8')
                image = client.parseDOM(network, 'img', ret='src')
                image = image[0].encode('utf-8')
                self.list.append({'name': title, 'url': self.tvmaze_link + u, 'image': image, 'action': 'tvshows'})

    except:
        networks = [('A&E', '/networks/29/ae', 'https://i.imgur.com/xLDfHjH.png'),
        ('ABC', '/networks/3/abc', 'https://i.imgur.com/qePLxos.png'),
        ('AMC', '/networks/20/amc', 'https://i.imgur.com/ndorJxi.png'),
        ('AT-X', '/networks/167/at-x', 'https://i.imgur.com/JshJYGN.png'),
        ('Adult Swim', '/networks/10/adult-swim', 'https://i.imgur.com/jCqbRcS.png'),
        ('Amazon', '/webchannels/3/amazon', 'https://i.imgur.com/ru9DDlL.png'),
        ('Animal Planet', '/networks/92/animal-planet', 'https://i.imgur.com/olKc4RP.png'),
        ('Audience', '/networks/31/audience-network', 'https://i.imgur.com/5Q3mo5A.png'),
        ('BBC America', '/networks/15/bbc-america', 'https://i.imgur.com/TUHDjfl.png'),
        ('BBC Four', '/networks/51/bbc-four', 'https://i.imgur.com/PNDalgw.png'),
        ('BBC One', '/networks/12/bbc-one', 'https://i.imgur.com/u8x26te.png'),
        ('BBC Three', '/webchannels/71/bbc-three', 'https://i.imgur.com/SDLeLcn.png'),
        ('BBC Two', '/networks/37/bbc-two', 'https://i.imgur.com/SKeGH1a.png'),
        ('BET', '/networks/56/bet', 'https://i.imgur.com/ZpGJ5UQ.png'),
        ('Bravo', '/networks/52/bravo', 'https://i.imgur.com/TmEO3Tn.png'),
        ('CBC', '/networks/36/cbc', 'https://i.imgur.com/unQ7WCZ.png'),
        ('CBS', '/networks/2/cbs', 'https://i.imgur.com/8OT8igR.png'),
        ('CTV', '/networks/48/ctv', 'https://i.imgur.com/qUlyVHz.png'),
        ('CW', '/networks/5/the-cw', 'https://i.imgur.com/Q8tooeM.png'),
        ('CW Seed', '/webchannels/13/cw-seed', 'https://i.imgur.com/nOdKoEy.png'),
        ('Cartoon Network', '/networks/11/cartoon-network', 'https://i.imgur.com/zmOLbbI.png'),
        ('Channel 4', '/networks/45/channel-4', 'https://i.imgur.com/6ZA9UHR.png'),
        ('Channel 5', '/networks/135/channel-5', 'https://i.imgur.com/5ubnvOh.png'),
        ('Cinemax', '/networks/19/cinemax', 'https://i.imgur.com/zWypFNI.png'),
        ('Comedy Central', '/networks/23/comedy-central', 'https://i.imgur.com/ko6XN77.png'),
        ('Crackle', '/webchannels/4/crackle', 'https://i.imgur.com/53kqZSY.png'),
        ('Discovery Channel', '/networks/66/discovery-channel', 'https://i.imgur.com/8UrXnAB.png'),
        ('Discovery ID', '/networks/89/investigation-discovery', 'https://i.imgur.com/07w7BER.png'),
        ('Discovery Science', '/networks/77/science', 'https://vignette.wikia.nocookie.net/logopedia/images/6/63/Discovery_Science_LA_2011.png/revision/latest?cb=20111129005128'),
        ('Disney Channel', '/networks/78/disney-channel', 'https://i.imgur.com/ZCgEkp6.png'),
        ('Disney XD', '/networks/25/disney-xd', 'https://i.imgur.com/PAJJoqQ.png'),
        ('E! Entertainment', '/networks/43/e', 'https://i.imgur.com/3Delf9f.png'),
        ('E4', '/networks/41/e4', 'https://i.imgur.com/frpunK8.png'),
        ('FOX', '/networks/4/fox', 'https://i.imgur.com/6vc0Iov.png'),
        ('FX', '/networks/13/fx', 'https://i.imgur.com/aQc1AIZ.png'),
        ('Freeform', '/networks/26/freeform', 'https://i.imgur.com/f9AqoHE.png'),
        ('HBO', '/networks/8/hbo', 'https://i.imgur.com/Hyu8ZGq.png'),
        ('HGTV', '/networks/192/hgtv', 'https://i.imgur.com/INnmgLT.png'),
        ('Hallmark', '/networks/50/hallmark-channel', 'https://i.imgur.com/zXS64I8.png'),
        ('History Channel', '/networks/53/history', 'https://i.imgur.com/LEMgy6n.png'),
        ('Hulu', '/webchannels/2/hulu', 'https://i.imgur.com/Vwx5QYJ.png'),
        ('ITV', '/networks/35/itv', 'https://i.imgur.com/5Hxp5eA.png'),
        ('Lifetime', '/networks/18/lifetime', 'https://i.imgur.com/tvYbhen.png'),
        ('MTV', '/networks/22/mtv', 'https://i.imgur.com/QM6DpNW.png'),
        ('NBC', '/networks/1/nbc', 'https://i.imgur.com/yPRirQZ.png'),
        ('National Geographic', '/networks/42/national-geographic-channel', 'https://i.imgur.com/XCGNKVQ.png'),
        ('Netflix', '/webchannels/1/netflix', 'https://i.imgur.com/jI5c3bw.png'),
        ('Nickelodeon', '/networks/27/nickelodeon', 'https://i.imgur.com/OUVoqYc.png'),
        ('PBS', '/networks/85/pbs', 'https://i.imgur.com/r9qeDJY.png'),
        ('Showtime', '/networks/9/showtime', 'https://i.imgur.com/SawAYkO.png'),
        ('Sky1', '/networks/63/sky-1', 'https://i.imgur.com/xbgzhPU.png'),
        ('Starz', '/networks/17/starz', 'https://i.imgur.com/Z0ep2Ru.png'),
        ('Sundance', '/networks/33/sundance-tv', 'https://i.imgur.com/qldG5p2.png'),
        ('Syfy', '/networks/16/syfy', 'https://i.imgur.com/9yCq37i.png'),
        ('TBS', '/networks/32/tbs', 'https://i.imgur.com/RVCtt4Z.png'),
        ('TLC', '/networks/80/tlc', 'https://i.imgur.com/c24MxaB.png'),
        ('TNT', '/networks/14/tnt', 'https://i.imgur.com/WnzpAGj.png'),
        ('TV Land', '/networks/57/tvland', 'https://i.imgur.com/1nIeDA5.png'),
        ('Travel Channel', '/networks/82/travel-channel', 'https://i.imgur.com/mWXv7SF.png'),
        ('TruTV', '/networks/84/trutv', 'https://i.imgur.com/HnB3zfc.png'),
        ('USA', '/networks/30/usa-network', 'https://i.imgur.com/Doccw9E.png'),
        ('VH1', '/networks/55/vh1', 'https://i.imgur.com/IUtHYzA.png'),
        ('WGN', '/networks/28/wgn-america', 'https://i.imgur.com/TL6MzgO.png')
        ]            
        for i in networks: self.list.append({'name': i[0], 'url': self.tvmaze_link + i[1], 'image': i[2], 'action': 'tvshows'})
        
    self.addDirectory(self.list)
    return self.list


def tvmaze_list(self, url):
    url2 = url
    items = []

    def maxpage(url):
        try:
            maxp = client.request(url + '&page=1000')
            maxp = client.parseDOM(maxp, 'ul', attrs = {'class': 'pagination'})
            maxp = client.parseDOM(maxp, 'li', attrs = {'class': 'current'})
            maxp = client.parseDOM(maxp, 'a')

            if not maxp:
                maxpage = 1
            else:
                maxpage = int(maxp[0])
            return maxpage
        except:
            return 1

    def getShows(url, choice):
        self.tvmaze_all_shows_link = 'http://www.tvmaze.com/shows?Show[network_id]=%s'#, 'http://www.tvmaze.com/webchannels?WebChannel[country_enum]=183&WebChannel[sort]=3']
        try:
            if choice == 0: url = self.tvmaze_all_shows_link % urlparse.urlparse(url).path.split('/')[2]
            for p in range(1, maxpage(url)+1):
                result = client.request(url + '&page=' + str(p))
                if choice == 0:
                    result = client.parseDOM(result, 'div', attrs = {'class': 'card primary grid-x'})
                else:
                    result = client.parseDOM(result, 'section', attrs = {'id': 'this-seasons-shows'})
                    
                for r in result:
                    itms = client.parseDOM(r, 'div', attrs = {'class': 'content auto cell'})
                    itms = [client.parseDOM(i, 'a', ret='href') for i in itms]
                    itms = [i[0] for i in itms if len(i) > 0]
                    itms = [re.findall('/(\d+)/', i) for i in itms]
                    itms = [i[0] for i in itms if len(i) > 0]
                    items.extend(itms)
            #return
        except:
            # try:
                # result = client.request(url2)
                # result = client.parseDOM(result, 'section', attrs = {'id': 'this-seasons-shows'})
                # items = client.parseDOM(result, 'div', attrs = {'class': 'content auto cell'})
                # items = [client.parseDOM(i, 'a', ret='href') for i in items]
                # items = [i[0] for i in items if len(i) > 0]
                # items = [re.findall('/(\d+)/', i) for i in items]
                # items = [i[0] for i in items if len(i) > 0]
                # items = items[:50]
            # except:
            return


    choice = xbmcgui.Dialog().select('All or Current TV Shows?',['All Shows', 'Current Shows'])
    getShows(url, choice)

    def items_list(i):
        try:
            url = self.tvmaze_info_link % i

            item = client.request(url)
            item = json.loads(item)

            title = item['name']
            title = re.sub('\s(|[(])(UK|US|AU|\d{4})(|[)])$', '', title)
            title = client.replaceHTMLCodes(title)
            title = title.encode('utf-8')

            year = item['premiered']
            year = re.findall('(\d{4})', year)[0]
            year = year.encode('utf-8')

            if int(year) > int((self.datetime).strftime('%Y')): raise Exception()

            imdb = item['externals']['imdb']
            if imdb == None or imdb == '': imdb = '0'
            else: imdb = 'tt' + re.sub('[^0-9]', '', str(imdb))
            imdb = imdb.encode('utf-8')

            tvdb = item['externals']['thetvdb']
            tvdb = re.sub('[^0-9]', '', str(tvdb))
            tvdb = tvdb.encode('utf-8')

            if tvdb == None or tvdb == '': raise Exception()

            try: poster = item['image']['original']
            except: poster = '0'
            if poster == None or poster == '': poster = '0'
            poster = poster.encode('utf-8')

            premiered = item['premiered']
            try: premiered = re.findall('(\d{4}-\d{2}-\d{2})', premiered)[0]
            except: premiered = '0'
            premiered = premiered.encode('utf-8')

            try: studio = item['network']['name']
            except: studio = '0'
            if studio == None: studio = '0'
            studio = studio.encode('utf-8')

            try: genre = item['genres']
            except: genre = '0'
            genre = [i.title() for i in genre]
            if genre == []: genre = '0'
            genre = ' / '.join(genre)
            genre = genre.encode('utf-8')

            try: duration = item['runtime']
            except: duration = '0'
            if duration == None: duration = '0'
            duration = str(duration)
            duration = duration.encode('utf-8')

            try: rating = item['rating']['average']
            except: rating = '0'
            if rating == None or rating == '0.0': rating = '0'
            rating = str(rating)
            rating = rating.encode('utf-8')

            try: plot = item['summary']
            except: plot = '0'
            if plot == None: plot = '0'
            plot = re.sub('<.+?>|</.+?>|\n', '', plot)
            plot = client.replaceHTMLCodes(plot)
            plot = plot.encode('utf-8')

            try: content = item['type'].lower()
            except: content = '0'
            if content == None or content == '': content = '0'
            content = content.encode('utf-8')

            self.list.append({'title': title, 'originaltitle': title, 'year': year, 'premiered': premiered, 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating, 'plot': plot, 'imdb': imdb, 'tvdb': tvdb, 'poster': poster, 'content': content})
        except:
            pass

    try:
        threads = []
        for i in items: threads.append(workers.Thread(items_list, i))
        [i.start() for i in threads]
        [i.join() for i in threads]

        filter = [i for i in self.list if i['content'] == 'scripted']
        filter += [i for i in self.list if not i['content'] == 'scripted']
        self.list = filter

        return self.list
    except:
        return

