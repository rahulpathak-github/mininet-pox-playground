from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.cli import CLI

class SimpleStarTopo(Topo):
    # overriding build function from the Topo class
    def build(self, n=4):
        switch = self.addSwitch('s1')
        for i in range(n):
            host = self.addHost('h'+str(i+1))
            self.addLink(host,switch)

# topos={'SimpleStarTopo':SimpleStarTopo}

if __name__ == '__main__':
    topo = SimpleStarTopo(n=4)
    network = Mininet(topo)
    network.start()
    print( "Dumping host connections" )
    dumpNodeConnections(network.hosts)
    # CLI(network)
    network.stop()
