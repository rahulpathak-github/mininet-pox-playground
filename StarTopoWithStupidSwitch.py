from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.node import RemoteController
from mininet.cli import CLI

class StarTopoWithStupidSwitch(Topo):
    # overriding build function from the Topo class
    def build(self):
        switch = self.addSwitch('s1')
        h1 = self.addHost('h1', mac='00:00:00:00:00:01', ip='10.0.0.2/24')
        h2 = self.addHost('h2', mac='00:00:00:00:00:02', ip='10.0.0.4/24')
        h3 = self.addHost('h3', mac='00:00:00:00:00:03', ip='10.0.0.5/24')
        h4 = self.addHost('h4', mac='00:00:00:00:00:04', ip='10.0.0.3/24')
        self.addLink(h1,switch)
        self.addLink(h2,switch)
        self.addLink(h3,switch)
        self.addLink(h4,switch)


if __name__ == '__main__':
    topo = StarTopoWithStupidSwitch()
    network = Mininet(topo, controller=RemoteController)
    network.start()
    print( "Dumping host connections" )
    dumpNodeConnections(network.hosts)
    CLI(network)
    network.stop()
