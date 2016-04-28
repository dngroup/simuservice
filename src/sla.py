import scipy
import scipy.integrate as integrate

tcp_win = 65535.0


def concurrentUsers(t, m, sigma, duration):
    return integrate.quad(
        lambda x: 1 / (sigma * scipy.sqrt(2 * scipy.pi) * scipy.exp(-(x - m) ** 2.0 / (2 * sigma ** 2))), t - duration,
        t)[0]


class Sla:
    def __init__(self, bitrate, count, time_span, movie_duration, start, cdn,max_cdn_to_use=2):
        self.start = start
        self.cdn = cdn
        self.delay = tcp_win / bitrate * 1000.0
        self.bandwidth = count * bitrate * movie_duration / time_span
        self.max_cdn_to_use=max_cdn_to_use

    def __str__(self):
        return "%d %d %lf %lf" % (self.start, self.cdn, self.delay, self.bandwidth)

        # Throughput = TCPWindow / round-trip-delay


def write_sla(sla, seed=None):
    with open("CDN.nodes.data", 'w') as f:
        f.write("%s \n" % sla.cdn)

    with open("starters.nodes.data", 'w') as f:
        f.write("%s \n" % sla.start)


def generate_random_slas(rs, substrate, count=1000):
    res = []
    for i in range(0, count):
        bitrate = rs.choice([500000, 750000,  1000000, 1500000, 2000000])
        #bitrate = rs.choice([500000, 1500000, 2500000])

        concurent_users = max(rs.normal(3000, 1000), 1000)
        time_span = max(rs.normal(24 * 60 * 60, 60 * 60), 0)
        movie_duration = max(rs.normal(60 * 60, 10 * 60), 0)

        start_count=rs.choice([1,2,3,4])
        end_count=2
        max_cdn_to_use=2

        draws = rs.choice(substrate.nodesdict.keys(), size=start_count+end_count, replace=False)
        start=draws[:-end_count]
        cdn=draws[-end_count:]

        res.append(Sla(bitrate, concurent_users, time_span, movie_duration, start, cdn,max_cdn_to_use=max_cdn_to_use))

    return res