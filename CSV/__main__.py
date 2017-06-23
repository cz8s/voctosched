#    Copyright (C) 2017  derpeter
#    derpeter@berlin.ccc.de
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


import configparser
import logging
import os
import sys
import csv

from fahrplan.datetime import parse_date, parse_datetime, parse_duration, parse_time
from fahrplan.model.conference import Conference
from fahrplan.model.event import Event
from fahrplan.model.schedule import Schedule
from fahrplan.slug.standard import StandardSlugGenerator


class main:
    """
    This class reads an CSV file and creates a schedule object from it.
    """

    def __init__(self):
        if not os.path.exists('config.conf'):
            raise IOError("config file not found")

        self.config = configparser.ConfigParser()
        self.config.read('config.conf')

        # set up logging
        logging.addLevelName(logging.WARNING, "\033[1;33m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
        logging.addLevelName(logging.ERROR, "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.ERROR))
        logging.addLevelName(logging.INFO, "\033[1;32m%s\033[1;0m" % logging.getLevelName(logging.INFO))
        logging.addLevelName(logging.DEBUG, "\033[1;85m%s\033[1;0m" % logging.getLevelName(logging.DEBUG))

        self.logger = logging.getLogger()

        ch = logging.StreamHandler(sys.stdout)
        if self.config['general']['debug']:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s {%(filename)s:%(lineno)d} %(message)s')
        else:
            formatter = logging.Formatter('%(asctime)s - %(message)s')

        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        self.logger.setLevel(logging.DEBUG)

        level = self.config['general']['debug']
        if level == 'info':
            self.logger.setLevel(logging.INFO)
        elif level == 'warning':
            self.logger.setLevel(logging.WARNING)
        elif level == 'error':
            self.logger.setLevel(logging.ERROR)
        elif level == 'debug':
            self.logger.setLevel(logging.DEBUG)

        self.type = self.config.get('source', 'type')
        self.source = self.config.get('source', 'source')
        self.output = self.config.get('general', 'output')

        logging.debug('reading ' + str(self.source) + ' from ' + self.type)

        # create the conference object
        self.conference = Conference(
            title=self.config.get('conference', 'title'),
            acronym=self.config.get('conference', 'acronym'),
            day_count=int(self.config.get('conference', 'day_count')),
            start=parse_date(self.config.get('conference', 'start')),
            end=parse_date(self.config.get('conference', 'end')),
            time_slot_duration=parse_duration(self.config.get('conference', 'time_slot_duration'))
        )

        self.slug = StandardSlugGenerator(self.conference)
        self.schedule = Schedule(conference=self.conference)
        self.license = self.config.get('conference', 'license')

        # decide where to get the CSV file
        if self.type == 'file':
            logging.info('reading CSV from file')
            self.generate_schedule()
            self.write_schedule()
        elif self.type == 'URL':
            self.downloadCSV()
        else:
            logging.error(str(self.type) + ' is not a valid source type')

    def readCSV(self):
        """
        read the given CSV
        :return:
        """
        pass

    def downloadCSV(self):
        """
        download a CSV file from an URL
        :return:
        """
        pass

    def generate_schedule(self):
        """
        Fill the schedule object with the events from the CSV
        :return:
        """
        with open(self.source, newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            for row in reader:
                self.schedule.add_room(row['Room'])
                self.schedule.add_event(int(row['Day']), row['Room'], Event(
                    uid=row['ID'],
                    date=parse_datetime(row['Date'] + 'T' + row['Start'] + ':00'),
                    start=parse_time(row['Start']),
                    duration=parse_duration(row['Duration']),
                    slug=self.slug,
                    title=row['Title'],
                    description=row.get('Description',''),
                    abstract=row.get('Abstract',''),
                    language=row['Language'],
                    persons={row['SpeakerID']: row['Speaker']},
                    download_url=row.get('File URL',''),
                    recording_license=self.license
                ))
        logging.debug(self.schedule.to_xml())

    def write_schedule(self):
        """
        write the schedule to a file
        :return:
        """
        with open(self.output, 'w', newline='') as outputfile:
            outputfile.write(self.schedule.to_xml())

if __name__ == '__main__':
    main()