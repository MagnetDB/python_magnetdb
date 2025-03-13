# import magnettools.Bmap as bmap
# import magnettools.magnettools as mt
import pandas as pd


def prepare_stress_map_chart_params(data, i_h, i_b, i_s, magnet_type):
    (Tubes, Helices, OHelices, BMagnets, UMagnets, Shims) = data
    icurrents = mt.get_currents(Tubes, Helices, BMagnets, UMagnets)

    return (
        i_h if i_h is not None else (icurrents[0] if len(icurrents) > 0 else 0),
        i_b if i_b is not None else (icurrents[1] if len(icurrents) > 1 else 0),
        i_s if i_s is not None else (icurrents[2] if len(icurrents) > 2 else 0),
        ["i_h", "i_b", "i_s"][:len(icurrents)],
        magnet_type if magnet_type is not None else "H",
    )


def compute_stress_map_chart(data, i_h: float, i_b: float, i_s: float, magnet_type: str):
    def update_current():
        (Tubes, Helices, OHelices, BMagnets, UMagnets, Shims) = data

        icurrents = mt.get_currents(Tubes, Helices, BMagnets, UMagnets)
        n_magnets = len(icurrents)
        mcurrents = icurrents
        print("n_magnets", n_magnets)
        print("icurrents", icurrents)
        # for j,Tube in enumerate(Tubes):
        #     print(f"Tube[{j}]: n_elem={Tube.get_n_elem()}, index={Tube.get_index()}")
        #     for i in range(Tube.get_n_elem()):
        #         print(f"H[{i}]: j={Helices[i + Tube.get_index()].get_CurrentDensity()}")
        Bz0 = mt.MagneticField(Tubes, Helices, BMagnets, UMagnets, 0, 0)[1]
        print("Bz0=", Bz0)

        # update Ih, Ib, Is range
        vcurrents = list(icurrents)
        num = 0
        if len(Tubes) != 0: vcurrents[num] = i_h; num += 1
        if len(BMagnets) != 0: vcurrents[num] = i_b; num += 1
        if len(UMagnets) != 0: vcurrents[num] = i_s; num += 1

        currents = mt.DoubleVector(vcurrents)
        print(f"currents= set to {vcurrents}")
        mt.set_currents(Tubes, Helices, BMagnets, UMagnets, OHelices, currents)
        print("actual currents", mt.get_currents(Tubes, Helices, BMagnets, UMagnets) )
        Bz0 = mt.MagneticField(Tubes, Helices, BMagnets, UMagnets, 0, 0)[1]
        print(f"Bz0={Bz0}")

    def sine():
        (Tubes, Helices, OHelices, BMagnets, UMagnets, Shims) = data
        mdata = {"H": Helices, "B": BMagnets, "S": UMagnets}
        Magnets = mdata[magnet_type]
        (headers, values) = bmap.getHoop(Magnets, Tubes, Helices, BMagnets, UMagnets, magnet_type)
        df = pd.DataFrame.from_records(values)
        df.columns = headers
        print(f'df = {df}')
        return (df['num'].tolist(), df['Hoop[MPa]'].tolist())

    def compute_max():
        (Tubes, Helices, OHelices, BMagnets, UMagnets, Shims) = data

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
        headers, Hoop_ = sine()
        return Hoop_

    update_current()
    x, y = sine()
    return dict(x=x, y=y, ymax=compute_max())
