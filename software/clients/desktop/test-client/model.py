# MIT License

# Copyright (c) 2021 Anderson R. Livramento

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sqlite3
import datetime

SAMPLE_TABLE = """
create table if not exists local_samples (
    id integer primary key,
    acquisition_date text not null,
    remote_id integer not null,
    sample_data text not null
);
"""

class LocalDBModel(object):

    def __init__(self, dbpath):
        self.db_file = '/'.join((dbpath, 'eyellow_local_samples.db'))
        self.conn = sqlite3.connect(self.db_file)

    def create_database(self):
        # Creating tables
        cursor = self.conn.cursor()
        cursor.execute(SAMPLE_TABLE)
        cursor.close()

    def insert_sample(self, remote_id, sample_data):
        sql = 'insert into local_samples(acquisition_date, remote_id, sample_data) values(?,?,?)'
        acquisition_date = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        cursor = self.conn.cursor()
        cursor.execute(sql, (acquisition_date, remote_id, sample_data))
        self.conn.commit()
        sample_id = cursor.lastrowid
        cursor.close()
        return sample_id

    def update_sample(self, sample_id, sample_data):
        sql = 'update local_samples set sample_data = ? where id = ?'
        cursor = self.conn.cursor()
        cursor.execute(sql, (sample_data, sample_id))
        self.conn.commit()
        cursor.close()

    def delete_sample(self, sample_id):
        sql = 'delete from local_samples where id = ?'
        cursor = self.conn.cursor()
        cursor.execute(sql, (sample_id,))
        self.conn.commit()
        cursor.close()

    def get_sample(self, sample_id):
        sql = 'select id, acquisition_date, remote_id, sample_data from local_samples where id = ?'
        cursor = self.conn.cursor()
        cursor.execute(sql, (sample_id,))
        sample = cursor.fetchone()
        cursor.close()
        return sample

    def close(self):
        self.conn.close()
