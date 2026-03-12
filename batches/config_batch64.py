"""
Batch 64 – Final sweep: remaining outer E/N/W postcodes + "contact us" style business searches:
E20, N9, N14, N18, NW7, UB3-UB8, HA0/HA2/HA5-HA9, EN4-EN8, more RM/IG postcodes,
plus "restaurant contact London", "cafe enquiries London", "food business London",
"eating out London [area]", "dining London [area]" for remaining areas
"""

SEARCH_QUERIES = [
    # E20 – Queen Elizabeth Olympic Park / Stratford International
    ("restaurants E20 London", "Restaurant", 50),
    ("cafes E20 London", "Cafe", 30),
    ("restaurants Olympic Park London E20", "Restaurant", 55),
    ("cafes Olympic Park London E20", "Cafe", 35),
    ("restaurants Westfield Stratford City London E20", "Restaurant", 55),
    ("cafes Westfield Stratford City London E20", "Cafe", 35),
    ("restaurants East Village London E20", "Restaurant", 45),
    ("cafes East Village London E20", "Cafe", 25),
    ("restaurants Stratford International London E20", "Restaurant", 45),
    ("cafes Stratford International London E20", "Cafe", 25),

    # N9 – Edmonton
    ("restaurants Edmonton London N9", "Restaurant", 50),
    ("cafes Edmonton London N9", "Cafe", 30),
    ("restaurants Lower Edmonton London N9", "Restaurant", 45),
    ("cafes Lower Edmonton London N9", "Cafe", 25),
    ("restaurants Fore Street Edmonton London N9", "Restaurant", 50),
    ("cafes Fore Street Edmonton London N9", "Cafe", 30),
    ("restaurants Church Street Edmonton London N9", "Restaurant", 45),
    ("cafes Church Street Edmonton London N9", "Cafe", 25),
    ("restaurants Silver Street Edmonton London N9", "Restaurant", 40),
    ("cafes Silver Street Edmonton London N9", "Cafe", 20),

    # N14 – Southgate
    ("restaurants Southgate London N14", "Restaurant", 50),
    ("cafes Southgate London N14", "Cafe", 30),
    ("restaurants Southgate High Street London N14", "Restaurant", 50),
    ("cafes Southgate High Street London N14", "Cafe", 30),
    ("restaurants Chase Road London N14", "Restaurant", 40),
    ("cafes Chase Road London N14", "Cafe", 20),
    ("restaurants Waterfall Road London N14", "Restaurant", 35),
    ("cafes Waterfall Road London N14", "Cafe", 20),

    # N18 – Upper Edmonton
    ("restaurants Upper Edmonton London N18", "Restaurant", 50),
    ("cafes Upper Edmonton London N18", "Cafe", 30),
    ("restaurants Hertford Road London N18", "Restaurant", 45),
    ("cafes Hertford Road London N18", "Cafe", 25),
    ("restaurants High Road Upper Edmonton London N18", "Restaurant", 50),
    ("cafes High Road Upper Edmonton London N18", "Cafe", 30),
    ("restaurants Fore Street Upper Edmonton London N18", "Restaurant", 45),
    ("cafes Fore Street Upper Edmonton London N18", "Cafe", 25),

    # NW7 – Mill Hill
    ("restaurants Mill Hill London NW7", "Restaurant", 50),
    ("cafes Mill Hill London NW7", "Cafe", 30),
    ("restaurants The Broadway Mill Hill London NW7", "Restaurant", 50),
    ("cafes The Broadway Mill Hill London NW7", "Cafe", 30),
    ("restaurants Bittacy Hill London NW7", "Restaurant", 35),
    ("cafes Bittacy Hill London NW7", "Cafe", 20),
    ("restaurants Holders Hill Road London NW7", "Restaurant", 35),
    ("cafes Holders Hill Road London NW7", "Cafe", 20),
    ("restaurants Page Street Mill Hill London NW7", "Restaurant", 35),
    ("cafes Page Street Mill Hill London NW7", "Cafe", 20),

    # UB3 – Hayes
    ("restaurants Hayes London UB3", "Restaurant", 50),
    ("cafes Hayes London UB3", "Cafe", 30),
    ("restaurants Station Road Hayes London UB3", "Restaurant", 45),
    ("cafes Station Road Hayes London UB3", "Cafe", 25),
    ("restaurants Uxbridge Road Hayes London UB3", "Restaurant", 50),
    ("cafes Uxbridge Road Hayes London UB3", "Cafe", 30),

    # UB4 – Hayes / Yeading
    ("restaurants Yeading London UB4", "Restaurant", 40),
    ("cafes Yeading London UB4", "Cafe", 20),
    ("restaurants Kingshill Avenue London UB4", "Restaurant", 35),
    ("cafes Kingshill Avenue London UB4", "Cafe", 20),

    # UB5 – Northolt
    ("restaurants Northolt London UB5", "Restaurant", 45),
    ("cafes Northolt London UB5", "Cafe", 25),
    ("restaurants Mandeville Road London UB5", "Restaurant", 40),
    ("cafes Mandeville Road London UB5", "Cafe", 20),
    ("restaurants Church Road Northolt London UB5", "Restaurant", 40),
    ("cafes Church Road Northolt London UB5", "Cafe", 20),

    # UB6 – Greenford
    ("restaurants Greenford London UB6", "Restaurant", 45),
    ("cafes Greenford London UB6", "Cafe", 25),
    ("restaurants Greenford Road London UB6", "Restaurant", 45),
    ("cafes Greenford Road London UB6", "Cafe", 25),
    ("restaurants Broadway Greenford London UB6", "Restaurant", 45),
    ("cafes Broadway Greenford London UB6", "Cafe", 25),

    # UB7 – West Drayton
    ("restaurants West Drayton London UB7", "Restaurant", 45),
    ("cafes West Drayton London UB7", "Cafe", 25),
    ("restaurants Station Road West Drayton London UB7", "Restaurant", 40),
    ("cafes Station Road West Drayton London UB7", "Cafe", 20),

    # UB8 – Uxbridge
    ("restaurants Uxbridge London UB8", "Restaurant", 50),
    ("cafes Uxbridge London UB8", "Cafe", 30),
    ("restaurants Uxbridge High Street London UB8", "Restaurant", 55),
    ("cafes Uxbridge High Street London UB8", "Cafe", 35),
    ("restaurants Windsor Street Uxbridge London UB8", "Restaurant", 40),
    ("cafes Windsor Street Uxbridge London UB8", "Cafe", 20),

    # HA0 – Wembley / Sudbury
    ("restaurants Sudbury London HA0", "Restaurant", 45),
    ("cafes Sudbury London HA0", "Cafe", 25),
    ("restaurants Harrow Road Wembley London HA0", "Restaurant", 50),
    ("cafes Harrow Road Wembley London HA0", "Cafe", 30),

    # HA2 – North Harrow / Rayners Lane
    ("restaurants North Harrow London HA2", "Restaurant", 45),
    ("cafes North Harrow London HA2", "Cafe", 25),
    ("restaurants Rayners Lane London HA2", "Restaurant", 45),
    ("cafes Rayners Lane London HA2", "Cafe", 25),

    # HA5 – Pinner
    ("restaurants Pinner London HA5", "Restaurant", 50),
    ("cafes Pinner London HA5", "Cafe", 30),
    ("restaurants High Street Pinner London HA5", "Restaurant", 50),
    ("cafes High Street Pinner London HA5", "Cafe", 30),

    # HA6 – Northwood
    ("restaurants Northwood London HA6", "Restaurant", 40),
    ("cafes Northwood London HA6", "Cafe", 20),
    ("restaurants Northwood Hills London HA6", "Restaurant", 40),
    ("cafes Northwood Hills London HA6", "Cafe", 20),

    # HA7 – Stanmore
    ("restaurants Stanmore London HA7", "Restaurant", 45),
    ("cafes Stanmore London HA7", "Cafe", 25),
    ("restaurants Church Road Stanmore London HA7", "Restaurant", 40),
    ("cafes Church Road Stanmore London HA7", "Cafe", 20),

    # HA8 – Edgware
    ("restaurants Edgware London HA8", "Restaurant", 50),
    ("cafes Edgware London HA8", "Cafe", 30),
    ("restaurants Station Road Edgware London HA8", "Restaurant", 50),
    ("cafes Station Road Edgware London HA8", "Cafe", 30),

    # HA9 – Wembley
    ("restaurants Wembley London HA9", "Restaurant", 55),
    ("cafes Wembley London HA9", "Cafe", 35),
    ("restaurants Wembley High Road London HA9", "Restaurant", 55),
    ("cafes Wembley High Road London HA9", "Cafe", 35),
    ("restaurants Wembley Central London HA9", "Restaurant", 50),
    ("cafes Wembley Central London HA9", "Cafe", 30),

    # EN4 – Hadley Wood / East Barnet / New Barnet
    ("restaurants East Barnet London EN4", "Restaurant", 40),
    ("cafes East Barnet London EN4", "Cafe", 20),
    ("restaurants New Barnet London EN4", "Restaurant", 40),
    ("cafes New Barnet London EN4", "Cafe", 20),

    # EN5 – Barnet
    ("restaurants Barnet London EN5", "Restaurant", 50),
    ("cafes Barnet London EN5", "Cafe", 30),
    ("restaurants High Street Barnet London EN5", "Restaurant", 50),
    ("cafes High Street Barnet London EN5", "Cafe", 30),
    ("restaurants Wood Street Barnet London EN5", "Restaurant", 40),
    ("cafes Wood Street Barnet London EN5", "Cafe", 20),

    # EN6 – Potters Bar
    ("restaurants Potters Bar London EN6", "Restaurant", 40),
    ("cafes Potters Bar London EN6", "Cafe", 20),
    ("restaurants High Street Potters Bar London EN6", "Restaurant", 40),
    ("cafes High Street Potters Bar London EN6", "Cafe", 20),

    # EN7 – Cheshunt / Goff's Oak
    ("restaurants Cheshunt London EN7", "Restaurant", 40),
    ("cafes Cheshunt London EN7", "Cafe", 20),

    # EN8 – Waltham Cross / Cheshunt
    ("restaurants Waltham Cross London EN8", "Restaurant", 40),
    ("cafes Waltham Cross London EN8", "Cafe", 20),
    ("restaurants High Street Waltham Cross London EN8", "Restaurant", 40),
    ("cafes High Street Waltham Cross London EN8", "Cafe", 20),

    # More RM/IG postcodes
    ("restaurants Chadwell Heath London RM6", "Restaurant", 40),
    ("cafes Chadwell Heath London RM6", "Cafe", 20),
    ("restaurants Rush Green London RM7", "Restaurant", 35),
    ("cafes Rush Green London RM7", "Cafe", 20),
    ("restaurants Collier Row London RM5", "Restaurant", 40),
    ("cafes Collier Row London RM5", "Cafe", 20),
    ("restaurants Harold Hill London RM3", "Restaurant", 40),
    ("cafes Harold Hill London RM3", "Cafe", 20),
    ("restaurants Emerson Park London RM11", "Restaurant", 35),
    ("cafes Emerson Park London RM11", "Cafe", 20),
    ("restaurants South Hornchurch London RM13", "Restaurant", 35),
    ("cafes South Hornchurch London RM13", "Cafe", 20),
    ("restaurants Redbridge London IG4", "Restaurant", 40),
    ("cafes Redbridge London IG4", "Cafe", 20),
    ("restaurants Clayhall London IG5", "Restaurant", 35),
    ("cafes Clayhall London IG5", "Cafe", 20),
    ("restaurants Woodford Green London IG8", "Restaurant", 40),
    ("cafes Woodford Green London IG8", "Cafe", 20),
    ("restaurants Chigwell Row London IG7", "Restaurant", 35),
    ("cafes Chigwell Row London IG7", "Cafe", 20),

    # "restaurant contact" / "cafe enquiries" style searches
    ("restaurant contact London", "Restaurant", 40),
    ("cafe enquiries London", "Cafe", 35),
    ("restaurant email London", "Restaurant", 40),
    ("food business contact London", "Restaurant", 40),
    ("restaurant bookings London EC1", "Restaurant", 35),
    ("restaurant reservations London EC2", "Restaurant", 35),
    ("restaurant reservations London WC1", "Restaurant", 35),
    ("restaurant reservations London SE1", "Restaurant", 35),
    ("restaurant reservations London E1", "Restaurant", 35),
    ("cafe contact London N1", "Cafe", 30),
    ("cafe contact London E8", "Cafe", 30),
    ("food business London enquiry", "Restaurant", 35),

    # "eating out" / "dining" remaining areas
    ("eating out Walthamstow London", "Restaurant", 40),
    ("eating out Leyton London", "Restaurant", 35),
    ("eating out Leytonstone London", "Restaurant", 35),
    ("eating out Stratford London", "Restaurant", 40),
    ("eating out Bow London", "Restaurant", 35),
    ("eating out Bethnal Green London", "Restaurant", 40),
    ("eating out Mile End London", "Restaurant", 35),
    ("eating out Whitechapel London", "Restaurant", 40),
    ("eating out Stepney London", "Restaurant", 35),
    ("eating out Catford London", "Restaurant", 35),
    ("eating out Lewisham London", "Restaurant", 40),
    ("eating out Forest Hill London", "Restaurant", 35),
    ("eating out Sydenham London", "Restaurant", 35),
    ("eating out Crystal Palace London", "Restaurant", 40),
    ("eating out Streatham London", "Restaurant", 40),
    ("eating out Norbury London", "Restaurant", 35),
    ("eating out Tooting London", "Restaurant", 40),
    ("dining Harlesden London NW10", "Restaurant", 40),
    ("dining Colindale London NW9", "Restaurant", 35),
    ("dining Cricklewood London NW2", "Restaurant", 40),
    ("dining Edmonton London N9", "Restaurant", 35),
    ("dining Upper Edmonton London N18", "Restaurant", 35),
    ("dining Enfield London EN1", "Restaurant", 40),
    ("dining Southgate London N14", "Restaurant", 35),
    ("dining Greenford London UB6", "Restaurant", 35),
    ("dining Northolt London UB5", "Restaurant", 35),
    ("dining Hayes London UB3", "Restaurant", 35),
    ("dining Wembley London HA9", "Restaurant", 40),
    ("dining Harrow London HA1", "Restaurant", 40),

    # Additional "food business" / "enquiry" style searches
    ("cafe contact us London EC1", "Cafe", 30),
    ("cafe contact us London N1", "Cafe", 30),
    ("restaurant website London E8", "Restaurant", 35),
    ("restaurant website London SE15", "Restaurant", 35),
    ("restaurant website London SW9", "Restaurant", 35),
    ("cafe website London NW1", "Cafe", 30),
    ("cafe website London E1", "Cafe", 30),
    ("restaurant email contact London NW10", "Restaurant", 35),
    ("food business contact London E17", "Restaurant", 30),
    ("food business contact London N15", "Restaurant", 30),
    ("food business contact London CR0", "Restaurant", 30),
    ("food business contact London UB1", "Restaurant", 30),

    # IG remaining postcodes
    ("restaurants Hainault London IG6", "Restaurant", 35),
    ("cafes Hainault London IG6", "Cafe", 20),
    ("restaurants Cranbrook London IG2", "Restaurant", 40),
    ("cafes Cranbrook London IG2", "Cafe", 20),
    ("restaurants Fairlop London IG6", "Restaurant", 30),
    ("cafes Fairlop London IG6", "Cafe", 20),
    ("restaurants Becontree London RM8", "Restaurant", 40),
    ("cafes Becontree London RM8", "Cafe", 20),
    ("restaurants Marks Gate London RM6", "Restaurant", 30),
    ("cafes Marks Gate London RM6", "Cafe", 20),

    # DA remaining postcodes
    ("restaurants Belvedere London DA17", "Restaurant", 35),
    ("cafes Belvedere London DA17", "Cafe", 20),
    ("restaurants Welling London DA16", "Restaurant", 40),
    ("cafes Welling London DA16", "Cafe", 20),
    ("restaurants Crayford London DA1", "Restaurant", 35),
    ("cafes Crayford London DA1", "Cafe", 20),
    ("restaurants Slade Green London DA8", "Restaurant", 30),
    ("cafes Slade Green London DA8", "Cafe", 20),
    ("restaurants Northumberland Heath London DA8", "Restaurant", 30),
    ("cafes Northumberland Heath London DA8", "Cafe", 20),

    # BR remaining postcodes
    ("restaurants Shortlands London BR2", "Restaurant", 35),
    ("cafes Shortlands London BR2", "Cafe", 20),
    ("restaurants Bickley London BR1", "Restaurant", 35),
    ("cafes Bickley London BR1", "Cafe", 20),
    ("restaurants Chislehurst London BR7", "Restaurant", 40),
    ("cafes Chislehurst London BR7", "Cafe", 20),
    ("restaurants St Mary Cray London BR5", "Restaurant", 35),
    ("cafes St Mary Cray London BR5", "Cafe", 20),
    ("restaurants West Wickham London BR4", "Restaurant", 35),
    ("cafes West Wickham London BR4", "Cafe", 20),

    # SM remaining postcodes
    ("restaurants Worcester Park London SM3", "Restaurant", 40),
    ("cafes Worcester Park London SM3", "Cafe", 20),
    ("restaurants Belmont London SM2", "Restaurant", 35),
    ("cafes Belmont London SM2", "Cafe", 20),
    ("restaurants Hackbridge London SM6", "Restaurant", 30),
    ("cafes Hackbridge London SM6", "Cafe", 20),
    ("restaurants Beddington London SM6", "Restaurant", 30),
    ("cafes Beddington London SM6", "Cafe", 20),

    # More "dining" area sweeps
    ("dining Norwood London SE27", "Restaurant", 35),
    ("dining Penge London SE20", "Restaurant", 35),
    ("dining Beckenham London BR3", "Restaurant", 40),
    ("dining Orpington London BR6", "Restaurant", 35),
    ("dining Sidcup London DA14", "Restaurant", 35),
    ("dining Bexleyheath London DA6", "Restaurant", 35),
    ("dining Chadwell Heath London RM6", "Restaurant", 30),
    ("dining Romford London RM1", "Restaurant", 40),
    ("dining Hornchurch London RM12", "Restaurant", 35),
    ("dining Upminster London RM14", "Restaurant", 30),
    ("dining Pinner London HA5", "Restaurant", 35),
    ("dining Stanmore London HA7", "Restaurant", 30),
    ("dining Edgware London HA8", "Restaurant", 35),
    ("dining Barnet London EN5", "Restaurant", 35),
    ("dining Mill Hill London NW7", "Restaurant", 35),
    ("dining Southgate London N14", "Restaurant", 35),
    ("dining Potters Bar London EN6", "Restaurant", 30),
]
