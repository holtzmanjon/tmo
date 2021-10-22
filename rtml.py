import pdb
from astropy.io import ascii

class Project() :
    """ class for an RTML Project
    """
    def __init__(self,user='holtz',email='holtz@nmsu.edu',organization='NMSU') :
        """ Initialize with user information
        """
        self.user=user 
        self.email=email
        self.organization=organization

    def open(self,file='test.xml') :
        """ Open RTML file for output with basic header
        """
        self.fout = open(file,'w')
        self.fout.write('<?xml version="1.0" encoding="ISO-8859-1"?>\n')
        self.fout.write('<RTML version="2.3">\n')
        self.fout.write('<Contact><User>{:s}</User>\n'.format(self.user))
        self.fout.write('<Email>{:s}</Email>\n'.format(self.email))
        self.fout.write('<Organization>{:s}</Organization></Contact>\n'.format(self.organization))

    def close(self) :
        """ Close RTML file
        """
        self.fout.write('</RTML>\n')
        self.fout.close()

    def write(self,request) :
        """ Write a target Request to RTML
        """
        self.fout.write('<Request bestefforts="True">\n')
        self.fout.write('<ID>{:s}</ID>\n'.format(request.targ))
        self.fout.write('<UserName>{:s}</UserName>\n'.format(request.user))
        self.fout.write('<Description>{:s}</Description>\n'.format(request.type))
        self.fout.write('<Reason>monitor={:d}</Reason>\n'.format(request.monitor))
        self.fout.write('<Project>{:s}</Project>\n'.format(request.project))
        self.fout.write('<Schedule>\n')
        self.fout.write('  <AirmassRange><Minimum>1</Minimum><Maximum>{:f}</Maximum></AirmassRange>\n'.format(request.airmax))
        self.fout.write('  <SkyCondition>Good</SkyCondition>\n')
        self.fout.write('  <Moon><Distance>20</Distance><Width>6</Width></Moon>\n')
        self.fout.write('  <Priority>{:d}</Priority>\n'.format(request.priority))
        self.fout.write('</Schedule>\n')
        self.fout.write('<Target count="{:d}" interval="0" tolerance="0">\n'.format(request.repeat))
        self.fout.write('  <Name>{:s}</Name>\n'.format(request.targ))
        self.fout.write('  <Coordinates><RightAscension>{:f}</RightAscension><Declination>{:f}</Declination></Coordinates>\n'.format(request.ra,request.dec))
        for exposure in request.exposures :
            filter=exposure[0]
            exptime=float(exposure[1])
            nexp=int(exposure[2])
            self.fout.write('  <Picture count="{:d}"><Name>{:s}</Name><Description>#nopreview </Description>\n'.format(nexp,request.targ))
            self.fout.write('    <ExposureTime>{:f}</ExposureTime><Binning>{:d}</Binning><Filter>{:s}</Filter>\n'.format(exptime,request.bin,filter))
            self.fout.write('  </Picture>\n')
        self.fout.write('</Target>\n')
        self.fout.write('</Request>\n')


class Request() :
    """ Class to hold target request information
    """

    def __init__(self,targ,user='NMSU',type='test',monitor=3,project='test',repeat=1,airmax=2,priority=5,ra=0,dec=0,bin=1,exposures=None) :
        self.targ = targ
        self.ra = ra
        self.dec = dec
        self.user = user
        self.type = type
        self.monitor = monitor
        self.project = project
        self.airmax = airmax
        self.priority = priority
        self.bin = bin
        self.repeat = repeat
        self.exposures = exposures

def coords(rah,ram,ras,decd,decm,decs) :
    """ routine to convert hms/dms to decimal
    """
    ra = (int(rah)+int(ram)/60.+float(ras)/3600)*15
    if '-' in decd:
        dec = abs(int(decd))+int(decm)/60.+float(decs)/3600.
        dec = -1 *dec
    else :
        dec = int(decd)+int(decm)/60.+float(decs)/3600.

    return ra, dec

def csv(file,user='NMSU',project='test') :
    """ Create RTML from a CSV file with individual targets and request configurations
    """
    out=Project()
    out.open(file+'.rtml')

    fp=open(file,'r')
    # input CSV format:
    # target,rah,ram,ras,decd,decm,decs,type,priority,monitor,airmax,repeat,bin,{nfilt}*[filter,exptime,count]
    for line in fp :
        fields=line.split(',')
        targ=fields[0]
        rah,ram,ras=fields[1:4]
        decd,decm,decs=fields[4:7]
        ra,dec=coords(rah,ram,ras,decd,decm,decs)
        type=fields[7]
        priority=int(fields[8])
        monitor=int(fields[9])
        airmax= float(fields[10])
        repeat=int(fields[11])
        bin=int(fields[12])
        nfilt=(len(fields)-13)//3
        i=13
        exposures=[]
        for ifilt in range(nfilt) :
            exposures.append([fields[i],fields[i+1],fields[i+2]])
            i+=3
        request=Request(targ,project=type,type=type,monitor=monitor,airmax=airmax,priority=priority,ra=ra,dec=dec,bin=bin,exposures=exposures,repeat=repeat)
        out.write(request)

    out.close()

def catalog(file,user='test',priority=5,airmax=2,monitor=0,repeat=1,bin=1,type='test',project='test',exposures=[['V','300','1'],['I','300','1']]) :    
    """ Create RTML from a catalog of targets, all with the same request configuration
    """

    out=Project()
    out.open(file+'.rtml')

    dat=ascii.read(file,delimiter='|')
    for line in dat :
        targ=line['col2']
        rah,ram,ras=line['col3'].split()
        decd,decm,decs=line['col4'].split()
        ra,dec=coords(rah,ram,ras,decd,decm,decs)

        request=Request(targ,user=user,project=project,type=type,monitor=monitor,airmax=airmax,priority=priority,ra=ra,dec=dec,bin=bin,exposures=exposures)
        out.write(request)

    out.close()

#catalog('Messier.txt',user='NMSU',project='Messier',type='Messier catalog',exposures=[['B','300','1'],['V','300','1'],['R','300','1']])
csv('planets.csv',user='NMSU',project='Planets')
