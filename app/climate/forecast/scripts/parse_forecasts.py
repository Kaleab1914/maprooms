import os
import calendar

def parse_seasonal_forecast_files(fcst_dir):
    full_months = list(calendar.month_name)[1:]
    short_months = list(calendar.month_abbr)[1:]
    year_dirs = [
        d for d in os.listdir(fcst_dir)
        if os.path.isdir(
            os.path.join(fcst_dir, d)
        )
    ]
    if len(year_dirs) == 0:
        raise ValueError('No years directory found')

    out = {'years': year_dirs, 'forecast': {}}

    for year in year_dirs:
        out['forecast'][year] = {}
        year_pth = os.path.join(fcst_dir, year)
        issued_dirs = [
            d for d in os.listdir(year_pth)
            if os.path.isdir(
                os.path.join(year_pth, d)
            )
        ]
        if len(issued_dirs) == 0:
            raise ValueError(
                f'No issuance directory found, year: {year}'
            )

        tmp_issue = []
        for i, v in enumerate(short_months):
            if v in issued_dirs:
                tmp_issue += [{'val': v, 'text': full_months[i]}]

        tmp_target = {}
        for issue in issued_dirs:
            issue_pth = os.path.join(year_pth, issue)
            target_dirs = [
                d for d in os.listdir(issue_pth)
                if os.path.isdir(
                    os.path.join(issue_pth, d)
                )
            ]
            if len(target_dirs) == 0:
                raise ValueError(
                    f'No target directory found, issued month: {issue}'
                )
            tmp_target[issue] = target_dirs

        out['forecast'][year]['issued'] = tmp_issue
        out['forecast'][year]['targets'] = tmp_target

    years = [int(y) for y in out['years']]
    ymax = max(years)
    issued = out['forecast'][str(ymax)]['issued']
    imon = [short_months.index(v['val']) for v in issued]
    mmax = short_months[max(imon)]
    targets = out['forecast'][str(ymax)]['targets'][mmax]
    mlen = []
    for t in targets:
        mo = []
        for m in t.split('-'):
            mo += [short_months.index(m)]
        if mo[0] < mo[1]:
            d = (mo[1] - mo[0]) + 1
        else:
            d = ((mo[1] - mo[0]) + 1) % 12
        mlen += [d]
    trgt = targets[mlen.index(min(mlen))]

    out['display'] = {
        'year': ymax,
        'month': mmax,
        'target': trgt
    }

    return out
