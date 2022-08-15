from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.util import dpid_to_str, str_to_dpid
from pox.lib.util import str_to_bool
import time
from pox.lib.addresses import EthAddr

log = core.getLogger()

_flood_delay = 0

class LearningSwitch (object):
    
  def __init__ (self, connection, transparent):
    self.connection = connection
    self.transparent = transparent
    self.macToPort = {}
    self.firewall = {}
    self.AddRule('00-00-00-00-00-01',EthAddr('00:00:00:00:00:01'))
    self.AddRule('00-00-00-00-00-01',EthAddr('00:00:00:00:00:02'))

    connection.addListeners(self)
    self.hold_down_expired = _flood_delay == 0
  
  def AddRule(self, dpidstr, src=0,value=True):
    self.firewall[(dpidstr,src)]=value
    log.debug("Adding firewall rule in %s: %s", dpidstr, src)
  
  def DeleteRule(self, dpidstr, src=0):
    try:
      del self.firewall[(dpidstr,src)]
      log.debug("Deleting firewall rule in %s: %s",
                 dpidstr, src)
    except KeyError:
      log.error("Cannot find in %s: %s",
                 dpidstr, src)
  
  def CheckRule(self, dpidstr,src=0):
    try:
      firewallEntry = self.firewall[(dpidstr,src)]
      # print(firewallEntry)
      if (firewallEntry == True):
        log.debug("Rule (%s) found in %s: FORWARD",
                  src, dpidstr)
      else:
        log.debug("Rule (%s) found in %s: DROP",
                  src, dpidstr)
      return firewallEntry
    except KeyError as e:
      # print(e)
      log.debug("Rule (%s) NOT found in %s: DROP",
                src, dpidstr)
      return False


  def _handle_PacketIn (self, event):

    packet = event.parsed

    def flood (message = None):
      msg = of.ofp_packet_out()
      if time.time() - self.connection.connect_time >= _flood_delay:

        if self.hold_down_expired is False:
          self.hold_down_expired = True
          log.info("%s: Flood hold-down expired -- flooding",
              dpid_to_str(event.dpid))

        if message is not None: log.debug(message)
        msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
      else:
        pass
      msg.data = event.ofp
      msg.in_port = event.port
      self.connection.send(msg)

    def drop (duration = None):
      if duration is not None:
        if not isinstance(duration, tuple):
          duration = (duration,duration)
        msg = of.ofp_flow_mod()
        msg.match = of.ofp_match.from_packet(packet)
        msg.idle_timeout = duration[0]
        msg.hard_timeout = duration[1]
        msg.buffer_id = event.ofp.buffer_id
        self.connection.send(msg)
      elif event.ofp.buffer_id is not None:
        msg = of.ofp_packet_out()
        msg.buffer_id = event.ofp.buffer_id
        msg.in_port = event.port
        self.connection.send(msg)

    self.macToPort[packet.src] = event.port
    dpidstr = dpid_to_str(event.connection.dpid)

    print(self.CheckRule(dpidstr,packet.src))

    if self.CheckRule(dpidstr, packet.src) == False:
      drop()
      return

    if not self.transparent:
      if packet.type == packet.LLDP_TYPE or packet.dst.isBridgeFiltered():
        print("LOL")
        drop()
        return

    if packet.dst.is_multicast:
      flood() 
    else:
      if packet.dst not in self.macToPort:
        flood("Port for %s unknown -- flooding" % (packet.dst,))
      else:
        port = self.macToPort[packet.dst]
        if port == event.port:
        
          log.warning("Same port for packet from %s -> %s on %s.%s.  Drop."
              % (packet.src, packet.dst, dpid_to_str(event.dpid), port))
          drop(10)
          return
        
        log.debug("installing flow for %s.%i -> %s.%i" %
                  (packet.src, event.port, packet.dst, port))
        msg = of.ofp_flow_mod()
        msg.match = of.ofp_match.from_packet(packet, event.port)
        msg.idle_timeout = 10
        msg.hard_timeout = 30
        msg.actions.append(of.ofp_action_output(port = port))
        msg.data = event.ofp
        self.connection.send(msg)


class l2_learning (object):

  def __init__ (self, transparent, ignore = None):

    core.openflow.addListeners(self)
    self.transparent = transparent
    self.ignore = set(ignore) if ignore else ()

  def _handle_ConnectionUp (self, event):
    if event.dpid in self.ignore:
      log.debug("Ignoring connection %s" % (event.connection,))
      return
    log.debug("Connection %s" % (event.connection,))
    LearningSwitch(event.connection, self.transparent)


def launch (transparent=False, hold_down=_flood_delay, ignore = None):
  try:
    global _flood_delay
    _flood_delay = int(str(hold_down), 10)
    assert _flood_delay >= 0
  except:
    raise RuntimeError("Expected hold-down to be a number")

  if ignore:
    ignore = ignore.replace(',', ' ').split()
    ignore = set(str_to_dpid(dpid) for dpid in ignore)

  core.registerNew(l2_learning, str_to_bool(transparent), ignore)
