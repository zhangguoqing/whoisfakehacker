import time
import scrapy


class OLBSpider(scrapy.Spider):
    name = "olb"

    def start_requests(self):
        urls = [
            # In https://github.com/search by
            # 'org:openstack repo:openstack' keyword
            'https://github.com/search?o=desc&q=org%3Aopenstack+repo%3Aopenstack&ref=searchresults&s=forks&type=Repositories&utf8=%E2%9C%93',
        ]

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        if response.status == 200:
            self.log('Github Search URL: %s' % response.url)
            launchpad_site = "https://bugs.launchpad.net/"
            # Launchpad Search filter optation
            # Order: by most recently changed
            # Status: Confirmed, Triaged, In Progress
            #         Fix Committed, Fix Released
            # Assignee: Doesn's matter
            launchpad_search_optation = '/+bugs?field.searchtext=&orderby=-date_last_updated&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.status%3Alist=FIXRELEASED&assignee_option=any&field.assignee=&field.bug_reporter=&field.bug_commenter=&field.subscriber=&field.structural_subscriber=&field.tag=&field.tags_combinator=ANY&field.has_cve.used=&field.omit_dupes.used=&field.omit_dupes=on&field.affects_me.used=&field.has_patch.used=&field.has_branches.used=&field.has_branches=on&field.has_no_branches.used=&field.has_no_branches=on&field.has_blueprints.used=&field.has_blueprints=on&field.has_no_blueprints.used=&field.has_no_blueprints=on&search=Search'
            for li in response.css('li.source'):
                project =  li.css('div.mb-1 a::attr(href)').extract_first()
                project_name = project[1:].split('/')[-1]
                url = launchpad_site + project_name + launchpad_search_optation
                yield scrapy.Request(url, callback=self.parseLaunchpad)

            # Search all openstac/* porjects which is about 1300, 100 pages
            next_page = response.css('a.next_page::attr(href)').extract_first()
            if next_page is not None:
                next_page = response.urljoin(next_page)
                time.sleep(5)
                yield scrapy.Request(next_page, callback=self.parse)

    def parseLaunchpad(self, response):
        if response.status == 200:
            self.log('Project URL: %s' % response.url)
            for bug in response.css('div.buglisting-row'):
                bugurl = bug.css("div.buginfo a::attr(href)").extract_first()
                yield scrapy.Request(bugurl, callback=self.parseBug)

            # Now, only checkout the first page which are the top75 of project.
            # next_page = response.css('a.next::attr(href)').extract_first()
            # if next_page is not None:
            #     next_page = response.urljoin(next_page)
            #     time.sleep(5)
            #     yield scrapy.Request(next_page, callback=self.parse)

    def parseBug(self, response):
        if response.status == 200:
            trs = response.xpath('//table[@id="affected-software"]/tbody/tr')
            if len(trs) > 2:
                yield {
                    'url': response.url,
                    'affects': len(trs) / 2,
                }
