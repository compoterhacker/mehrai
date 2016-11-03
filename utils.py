import time, sys, string, json
import urllib, urllib2, hashlib, os
import itertools, mimetools, mimetypes, pipes
PRINTABLE_CHARACTERS = string.letters + string.digits + string.punctuation + " "
VIPER_URL_ADD = "http://viper:8080/file/add"


def convert2printable(s):
    if not isinstance(s, basestring) or isPrintable(s):
        return s
    return "".join(convertChar(c) for c in s)


def convertChar(c):
    if c in PRINTABLE_CHARACTERS:
        return c
    else:
        return "?"


def isPrintable(s):
    for c in s:
        if not c in PRINTABLE_CHARACTERS:
            return False
    return True


def get_sha256(fileName):
    hash = hashlib.sha256()
    with open(fileName) as f:
        for chunk in iter(lambda: f.read(4096), ""):
            hash.update(chunk)
    return hash.hexdigest()


def getTelnetPid(self):
    pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]
    for pid in pids:
        leProc = open('/proc/%s/cmdline' % pid).read().split('\0')
        if leProc[0] is '/bin/telnetd':
            return int(pid)


def args_to_string(args):
    return ' '.join(map(lambda x: pipes.quote(str(x)), args) or [])


def convertDirtyDict2ASCII(data):
    if data is None or isinstance(data, (bool, int, long, float)):
        return data
    if isinstance(data, basestring):
        return convert2printable(data)
    if isinstance(data, list):
        return [convertDirtyDict2ASCII(val) for val in data]
    if isinstance(data, OrderedDict):
        return [[convertDirtyDict2ASCII(k), convertDirtyDict2ASCII(v)] for k, v in data.iteritems()]
    if isinstance(data, dict):
        if all(isinstance(k, basestring) for k in data):
            return {k: convertDirtyDict2ASCII(v) for k, v in data.iteritems()}
        return [[convertDirtyDict2ASCII(k), convertDirtyDict2ASCII(v)] for k, v in data.iteritems()]
    if isinstance(data, tuple):
        return [convertDirtyDict2ASCII(val) for val in data]
    if isinstance(data, set):
        return [convertDirtyDict2ASCII(val) for val in data]
    
    return data


class MultiPartForm(object):
    """Accumulate the data to be used when posting a form."""

    def __init__(self):
        self.form_fields = []
        self.files = []
        self.boundary = mimetools.choose_boundary()
        return
    

    def get_content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary


    def add_field(self, name, value):
        value = convertDirtyDict2ASCII(value)
        
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))
        return


    def add_file(self, fieldname, filename, fileHandle, mimetype=None):
        filename = convertDirtyDict2ASCII(filename)
        
        """Add a file to be uploaded."""
        body = fileHandle.read()
        if mimetype is None:
            mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        self.files.append((fieldname, filename, mimetype, body))
        return
    

    def add_file_data(self, fieldname, filename, file_data, mimetype=None):
        filename = convertDirtyDict2ASCII(filename)
        
        """Add a file to be uploaded."""
        if mimetype is None:
            mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        self.files.append((fieldname, filename, mimetype, file_data))
        return


    def __str__(self):
        """Return a string representing the form data, including attached files."""
        # Build a list of lists, each containing "lines" of the
        # request.  Each part is separated by a boundary string.
        # Once the list is built, return a string where each
        # line is separated by '\r\n'.  
        parts = []
        part_boundary = '--' + self.boundary
        
        # Add the form fields
        parts.extend(
            [ part_boundary,
              'Content-Disposition: form-data; name="%s"' % name,
              '',
              value,
            ]
            for name, value in self.form_fields
            )
        
        # Add the files to upload
        parts.extend(
            [ part_boundary,
              'Content-Disposition: file; name="%s"; filename="%s"' % \
                 (field_name, filename),
              'Content-Type: %s' % content_type,
              '',
              body,
            ]
            for field_name, filename, content_type, body in self.files
            )
        
        # Flatten the list and add closing boundary marker,
        # then return CR+LF separated data
        flattened = list(itertools.chain(*parts))
        flattened.append('--' + self.boundary + '--')
        flattened.append('')
        return '\r\n'.join(flattened)


def upload(filePath):
    rawFile = open(filePath, 'rb')

    try:
        form = MultiPartForm()
        form.add_file('file', filePath, fileHandle=rawFile)
        form.add_field('tags', 'mehrai')
    
        request = urllib2.Request(VIPER_URL_ADD)
        body = str(form)

        request.add_header('Content-type', form.get_content_type())
        request.add_header('Content-length', len(body))
        request.add_data(body)
    
        response_data = urllib2.urlopen(request).read() 
        reponsejson = json.loads(response_data)
        
    except urllib2.URLError as e:
        print "[!] File already exists: %s" % e
        pass
    except ValueError as e:
        print "Unable to convert response to JSON: %s" % e
        pass