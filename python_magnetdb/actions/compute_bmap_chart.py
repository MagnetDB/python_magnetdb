# import magnettools.Bmap as bmap
# import magnettools.magnettools as mt
import numpy as np


plotmethod = {
    # 'Bz': (bmap.getBz, '[T]', 'Magnetic Field Bz'),
    # 'Br': (bmap.getBr, '[T]', 'Magnetic Field Bz'),
    # 'B': (bmap.getB, '[T]', 'Magnetic Field'),
    # 'A': (bmap.getA, '[A/m]', 'Magnetic Potential'),
    # 'dBr/dr': (bmap.getdBrdr, '[T/m]', 'Gradient of Magnetic Field Br'),
    # 'dBr/dz': (bmap.getdBrdz, '[T/m]', 'Gradient of Magnetic Field Br'),
    # 'dBz/dr': (bmap.getdBzdr, '[T/m]', 'Gradient of Magnetic Field Bz'),
    # 'dBz/dz': (bmap.getdBzdz, '[T/m]', 'Gradient of Magnetic Field Bz'),
    # 'G': (bmap.getGradMagnetoGravPotential, '[%]', 'He Levitation Force Homogeneity')
    # 'd²Bz/dz²': (bmap.getd2Bzdz2, '[T/m²]', 'Second order Derivative of Magnetic Field Bz'),
}


def prepare_bmap_chart_params(data, i_h, i_b, i_s, n, r0, z0, r, z, pkey, command):
    # when UMagnets, add hts.json to data??
    (Tubes,Helices,OHelices,BMagnets,UMagnets,Shims) = data
    icurrents = mt.get_currents(Tubes, Helices, BMagnets, UMagnets)
    print(f'prepare_bmap_chart_params: pkey={pkey}, icurrents={[current for current in icurrents]}')

    return (
        i_h if i_h is not None else (icurrents[0] if len(icurrents) > 0 else 0),
        i_b if i_b is not None else (icurrents[1] if len(icurrents) > 1 else 0),
        i_s if i_s is not None else (icurrents[2] if len(icurrents) > 2 else 0),
        n if n is not None else 160,
        r0 if r0 is not None else 0,
        z0 if z0 is not None else 0,
        r if r is not None else (0, 1.00),
        z if z is not None else (-1.00, 1.00),
        pkey if pkey is not None else "Bz",
        command if command is not None else "1D_z",
        ["i_h", "i_b", "i_s"][:len(icurrents)],
    )


def compute_bmap_chart(data, i_h, i_b, i_s, n, r0, z0, r, z, pkey, command):
    def update_current():
        (Tubes,Helices,OHelices,BMagnets,UMagnets,Shims) = data

        icurrents = mt.get_currents(Tubes, Helices, BMagnets, UMagnets)
        n_magnets = len(icurrents)
        mcurrents = icurrents
        # print("n_magnets", n_magnets)
        # print("icurrents", icurrents)
        # for j,Tube in enumerate(Tubes):
        #     print(f"Tube[{j}]", Tube.get_n_elem(), Tube.get_index())
        #     for i in range(Tube.get_n_elem()):
        #         print(f"H[{i}]: j={Helices[i + Tube.get_index()].get_CurrentDensity()}")
        Bz0 = mt.MagneticField(Tubes, Helices, BMagnets, UMagnets, 0, 0)[1]
        print(f"Bz0={Bz0} T")

        # update Ih, Ib, Is range
        vcurrents = list(icurrents)
        num = 0
        if len(Tubes) != 0: vcurrents[num] = i_h; num += 1
        if len(BMagnets) != 0: vcurrents[num] = i_b; num += 1
        if len(UMagnets) != 0: vcurrents[num] = i_s; num += 1

        currents = mt.DoubleVector(vcurrents)
        print(f"currents= set to {vcurrents}")
        mt.set_currents(Tubes, Helices, BMagnets, UMagnets, OHelices, currents)
        print(f"actual currents={mt.get_currents(Tubes, Helices, BMagnets, UMagnets)}" )
        Bz0 = mt.MagneticField(Tubes, Helices, BMagnets, UMagnets, 0, 0)[1]
        print(f"Bz0={Bz0} T")

    def sine():
        # print("panel_bmap: compute b")
        (Tubes,Helices,OHelices,BMagnets,UMagnets,Shims) = data
        if command == '1D_z':
            x = np.linspace(z[0], z[1], n)
            if pkey in ['G']:
                B_ = np.vectorize(plotmethod[pkey][0], excluded=[0, 2, 3, 4, 5, 6])
                Bval = lambda y: B_(r0, x, Tubes, Helices, BMagnets, UMagnets, Shims, G0)
            elif pkey in ['dBr/dr', 'dBr/dz', 'dBz/dr', 'dBz/dz']:
                B_ = np.vectorize(plotmethod[pkey][0], excluded=[0, 2, 3, 4, 5, 6])
                Bval = lambda y: B_(r0, x, Tubes, Helices, BMagnets, UMagnets, Shims)
            else:
                B_ = np.vectorize(plotmethod[pkey][0], excluded=[0, 2, 3, 4, 5])
                Bval = lambda y: B_(r0, x, Tubes, Helices, BMagnets, UMagnets)
            return x, Bval(x)

        if command == '1D_r':
            x = np.linspace(r[0], r[1], n)
            if pkey in ['G']:
                B_ = np.vectorize(plotmethod[pkey][0], excluded=[1, 2, 3, 4, 5, 6])
                Bval = lambda y: B_(x, y, Tubes, Helices, BMagnets, UMagnets, Shims, G0)
            elif pkey in ['dBr/dr', 'dBr/dz', 'dBz/dr', 'dBz/dz']:
                B_ = np.vectorize(plotmethod[pkey][0], excluded=[1, 2, 3, 4, 5, 6])
                Bval = lambda y: B_(x, y, Tubes, Helices, BMagnets, UMagnets, Shims)
            else:
                B_ = np.vectorize(plotmethod[pkey][0], excluded=[1, 2, 3, 4, 5])
                Bval = lambda y: B_(x, z0, Tubes, Helices, BMagnets, UMagnets)
            return x, Bval(x)

    def compute_max():
        (Tubes,Helices,OHelices,BMagnets,UMagnets,Shims) = data

        # get current for max
        icurrents = mt.get_currents(Tubes, Helices, BMagnets, UMagnets)
        vcurrents = list(icurrents)
        num = 0
        if len(Tubes) != 0: vcurrents[num] = 31.e+3; num += 1
        if len(BMagnets) != 0: vcurrents[num] = 31.e+3; num += 1
        if len(UMagnets) != 0: vcurrents[num] = 0; num += 1

        Bz0 = mt.MagneticField(Tubes, Helices, BMagnets, UMagnets, 0, 0)[1]

        currents = mt.DoubleVector(vcurrents)
        mt.set_currents(Tubes, Helices, BMagnets, UMagnets, OHelices, currents)
        x, y = sine()
        return y

    update_current()
    x, y = sine()

    return dict(x=x.tolist(), y=y.tolist(), ymax=compute_max().tolist(), yaxis=plotmethod[pkey][1])
