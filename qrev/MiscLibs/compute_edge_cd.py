def compute_edge_cd(edge_data):
    """Computes the edge shape coefficient used to determine the visual shape of
    the edge if other than rectangular or triangular.

    Parameters
    ----------
    edge_data: EdgeData
        Object of EdgeData

    Returns
    -------
    cd: float
        Edge shape coefficient
    """

    if edge_data.type == "User Q":
        cd = 0.5
    else:
        ca = (((edge_data.cust_coef - 0.3535) / (0.92 - 0.3535)) * (1 - 0.5)) + 0.5
        cd = (ca - 0.5) * 2
    return cd