"""Sky-position coverage queries: absence, coverage, and failure are distinct."""

def target_coordinates(args):
    from astropy.coordinates import SkyCoord
    from astroquery.mast import Catalogs
    if args.tic is not None:
        table=Catalogs.query_criteria(catalog="TIC",ID=str(args.tic))
        exact=[row for row in table if str(row["ID"])==str(args.tic)]
        if len(exact)!=1:raise ValueError("TIC catalog lookup did not give one exact identifier")
        row=exact[0];ra=float(row["ra"]);dec=float(row["dec"])
        return SkyCoord(ra,dec,unit="deg",frame="icrs"),{
            "tic":args.tic,"ra_deg":ra,"dec_deg":dec,"coordinates":"TIC catalog position"}
    return SkyCoord(args.ra,args.dec,unit="deg",frame="icrs"),{
        "tic":None,"ra_deg":args.ra,"dec_deg":args.dec,"coordinates":"input ICRS position"}


def discover(coords):
    from astroquery.mast import Tesscut
    table=Tesscut.get_sectors(coordinates=coords)
    rows=[]
    for row in table:
        rows.append({"sector":int(row["sector"]),"camera":int(row["camera"]),
                     "ccd":int(row["ccd"])})
    rows=sorted({(r["sector"],r["camera"],r["ccd"]) for r in rows})
    return [{"sector":s,"camera":c,"ccd":d} for s,c,d in rows]
