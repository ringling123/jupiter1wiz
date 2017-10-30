"""
    urlresolver XBMC Addon
    Copyright (C) 2011 t0mm0

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
"""
from __generic_resolver__ import GenericResolver

class VidCrazyResolver(GenericResolver):
    name = 'vidcrazy.net'
    domains = ['vidcrazy.net', 'uploadcrazy.net']
    pattern = '(?://|\.)(vidcrazy.net|uploadcrazy.net)/\D+.php\?file=([0-9a-zA-Z\-_]+)'

    def get_url(self, host, media_id):
        return self._default_get_url('uploadcrazy.net', media_id, template='http://{host}/embed.php?file={media_id}')
