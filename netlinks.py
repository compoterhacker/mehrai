from ctypes import *
import socket
import os

AF_NETLINK = PF_NETLINK = 16
NETLINK_CONNECTOR = 11
NLMSG_DONE = 3
CN_IDX_PROC = 1
CN_VAL_PROC = 1
PROC_CN_MCAST_LISTEN = 1
PROC_CN_MCAST_IGNORE = 2

event_types = {
    'FORK': 0x00000001,
    'EXEC': 0x00000002,
    'UID': 0x00000004,
    'GID': 0x00000040,
    'SID': 0x00000080,
    'PTRACE': 0x00000100,
    'COMM': 0x00000200,
    'COREDUMP': 0x40000000,
    'EXIT': 0x80000000
}

class nlmsghdr(Structure):
    _fields_ = [
        ('nlmsg_len', c_uint),
        ('nlmsg_type', c_ushort),
        ('nlmsg_flags', c_ushort),
        ('nlmsg_seq', c_uint),
        ('nlmsg_pid', c_uint),
    ]

class cb_id(Structure):
    _fields_ = [
        ('idx', c_uint),
        ('val', c_uint),
    ]

class cn_msg(Structure):
    _fields_ = [
        ('id', cb_id),
        ('seq', c_uint),
        ('ack', c_uint),
        ('len', c_ushort),
        ('flags', c_ushort),
    ]

class event_data_ack(Structure):
    _fields_ = [
        ('err', c_uint)
    ]

class event_data_fork_proc_event(Structure):
    _fields_ = [
        ('parent_pid', c_int),
        ('parent_tgid', c_int),
        ('child_pid', c_int),
        ('child_tgid', c_int),
    ]

class event_data_exec_proc_event(Structure):
    _fields_ = [
        ('process_pid', c_int),
        ('process_tgid', c_int),
    ]

class uid_gid(Union):
    _fields_ = [
        ('uid', c_uint),
        ('gid', c_uint),
    ]

class event_data_id_proc_event(Structure):
    _fields_ = [
        ('process_pid', c_int),
        ('process_tgid', c_int),
        ('r', uid_gid),
        ('e', uid_gid),
    ]

class event_data_sid_proc_event(Structure):
    _fields_ = [
        ('process_pid', c_int),
        ('process_tgid', c_int),
    ]

class event_data_ptrace_proc_event(Structure):
    _fields_ = [
        ('process_pid', c_int),
        ('process_tgid', c_int),
        ('tracer_pid', c_int),
        ('tracer_tgid', c_int),

    ]

class event_data_comm_proc_event(Structure):
    _fields_ = [
        ('process_pid', c_int),
        ('process_tgid', c_int),
        ('comm', c_char * 16)
    ]

class event_data_coredump_proc_event(Structure):
    _fields_ = [
        ('process_pid', c_int),
        ('process_tgid', c_int)
    ]

class event_data_exit_proc_event(Structure):
    _fields_ = [
        ('process_pid', c_int),
        ('process_tgid', c_int),
        ('exit_code', c_uint),
        ('exit_signal', c_uint),
    ]

class event_data(Union):
    _fields_ = [
        ('ack', event_data_ack),
        ('fork', event_data_fork_proc_event),
        ('_exec', event_data_exec_proc_event),
        ('id', event_data_id_proc_event),
        ('sid', event_data_sid_proc_event),
        ('ptrace', event_data_ptrace_proc_event),
        ('comm', event_data_comm_proc_event),
        ('coredump', event_data_coredump_proc_event),
        ('exit', event_data_exit_proc_event),
    ]

class proc_event(Structure):
    _fields_ = [
        ('what', c_uint),
        ('cpu', c_uint),
        ('timestamp_ns', c_ulonglong),
        ('event_data', event_data)
    ]

class nlcn_msg_mcast(Structure):
    _fields_ = [
        ('nl_hdr', nlmsghdr),
        ('cn_msg', cn_msg),
        ('cn_mcast', c_uint)
    ]

class nlcn_msc_proc_event(Structure):
    _fields_ = [
        ('nl_hdr', nlmsghdr),
        ('cn_msg', cn_msg),
        ('proc_ev', proc_event)
    ]

class NetlinkConnector():
    def __init__(self):
        self.sock = socket.socket(PF_NETLINK, socket.SOCK_DGRAM, NETLINK_CONNECTOR)
        self.sock.bind((os.getpid(), CN_IDX_PROC))

        self.toggle_mcast()

    def toggle_mcast(self, enabled=True):
        listen_msg = nlcn_msg_mcast()
        listen_msg.nl_hdr.nlmsg_len = sizeof(nlcn_msg_mcast)
        listen_msg.nl_hdr.nlmsg_pid = os.getpid()
        listen_msg.nl_hdr.nlmsg_type = NLMSG_DONE

        listen_msg.cn_msg.id.idx = CN_IDX_PROC
        listen_msg.cn_msg.id.val = CN_VAL_PROC
        listen_msg.cn_msg.len = sizeof(c_uint)

        listen_msg.cn_mcast = PROC_CN_MCAST_LISTEN if enabled else PROC_CN_MCAST_IGNORE

        self.sock.send(listen_msg)

    def recv(self):
        sock_data = self.sock.recv(sizeof(nlcn_msc_proc_event))

        event_data = proc_event()
        memmove(addressof(event_data), sock_data[-40:], sizeof(proc_event))

        what = event_data.what

        events = []

        if not what:
            events.append({
                'event': 'NONE',
                'error': event_data.event_data.ack.err
            })
        if what & event_types['FORK']:
            events.append({
                'event': 'FORK',
                'parent_pid': event_data.event_data.fork.parent_pid,
                'parent_tgid': event_data.event_data.fork.parent_tgid,
                'child_pid': event_data.event_data.fork.child_pid,
                'child_tgid': event_data.event_data.fork.child_tgid
            })
        if what & event_types['EXEC']:
            events.append({
                'event': 'EXEC',
                'process_pid': event_data.event_data._exec.process_pid,
                'process_tgid': event_data.event_data._exec.process_tgid
            })
        if what & event_types['UID']:
            events.append({
                'event': 'ID',
                'process_pid': event_data.event_data.id.process_pid,
                'process_tgid': event_data.event_data.id.process_tgid,
                'real_uid': event_data.event_data.id.r.uid,
                'effective_uid': event_data.event_data.id.e.uid,
            })
        if what & event_types['GID']:
            events.append({
                'event': 'GID',
                'process_pid': event_data.event_data.id.process_pid,
                'process_tgid': event_data.event_data.id.process_tgid,
                'real_gid': event_data.event_data.id.r.gid,
                'effective_gid': event_data.event_data.id.e.gid,
            })
        if what & event_types['SID']:
            events.append({
                'event': 'SID',
                'process_pid': event_data.event_data.sid.process_pid,
                'process_tgid': event_data.event_data.sid.process_tgid,
            })
        if what & event_types['PTRACE']:
            events.append({
                'event': 'PTRACE',
                'process_pid': event_data.event_data.ptrace.process_pid,
                'process_tgid': event_data.event_data.ptrace.process_tgid,
                'tracer_pid': event_data.event_data.ptrace.tracer_pid,
                'tracer_tgid': event_data.event_data.ptrace.tracer_tgid,
            })
        if what & event_types['COMM']:
            events.append({
                'event': 'COMM',
                'process_pid': event_data.event_data.comm.process_pid,
                'process_tgid': event_data.event_data.comm.process_tgid,
                'comm': event_data.event_data.comm.comm
            })
        if what & event_types['COREDUMP']:
            events.append({
                'event': 'COREDUMP',
                'process_pid': event_data.event_data.coredump.process_pid,
                'process_tgid': event_data.event_data.coredump.process_tgid
            })
        if what & event_types['EXIT']:
            events.append({
                'event': 'EXIT',
                'process_pid': event_data.event_data.exit.process_pid,
                'process_tgid': event_data.event_data.exit.process_tgid,
                'exit_code': event_data.event_data.exit.exit_code,
                'exit_signal': event_data.event_data.exit.exit_signal
            })
        
        return events


    def close(self):
        self.toggle_mcast(False)
        self.sock.close()


    def fileno(self):
        return self.sock.fileno()


def pid_to_exe(pid):
    try:
        return os.readlink('/proc/%d/exe' % pid)
    except OSError:
        return ''


def pid_to_cmdline(pid):
    try:
        return open('/proc/%d/cmdline' % pid).read().split('\0')
    except IOError:
        return ''