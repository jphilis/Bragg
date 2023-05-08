import time
import ROOT
from initiate import initiate_garfield

PLOT_TIME = 5
class Solid:
        def __init__(self, path, gf, plot_time):
            self.path = path
            self.gf = gf
            self.plot_time = plot_time

            self.center_x, self.center_y, self.center_z = 0, 5, 0
            self.len_x, self.len_y, self.len_z = 5, 5, 5
            self.medium = self.gf.MediumSilicon()

            self.cmp_const = None
            self.geometry = None
            self.view = None

        def setup_geometry(self):
            self.geometry = self.gf.GeometrySimple()
            self.geometry.SetMedium(self.gf.MediumSilicon())

        def create_box(self, cx, cy, cz, lx, ly, lz):
            """c is center, l is half-width"""
            # self.box = self.gf.SolidBox(
            #     self.center_x, self.center_y, self.center_z,
            #     self.len_x, self.len_y, self.len_z,
            # )
            box = self.gf.SolidBox(cx, cy, cz, lx, ly, lz)
            self.geometry.AddSolid(box, self.medium)

        def create_tube(self, cx, cy, cz, r, lz, dx, dy, dz):
            """c is center, r is radius l is half-length,
            (dx, dy, dz) is the direction of the cylinder.
            """
            tube = self.gf.SolidTube(cx, cy, cz, r, lz, dx, dy, dz)
            self.geometry.AddSolid(tube, self.medium)

        def view_solid(self):
            self.view = self.gf.ViewGeometry()
            self.view.SetGeometry(self.geometry)
            self.view.Plot()

        def main(self):
            self.setup_geometry()
            # self.create_box(0, 5, 0, 5, 5, 5)
            self.create_tube(0, 0, 0, 5, 5, 0, 1, 0)
            self.view_solid()

            time.sleep(self.plot_time)


def main():
    path, gf = initiate_garfield()
    solid = Solid(path, gf, PLOT_TIME)
    solid.main()


if __name__ == "__main__":
    main()