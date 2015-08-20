import shutil

__author__ = 'Jason Grundstad'
from django.conf import settings
from viewer.models import Variant, Report
import json
import os
import tablib


variant_headers = {'chr': 'str',
                   'pos': 'int',
                   'ref': 'str',
                   'alt': 'str',
                   'normal_ref_count': 'int',
                   'normal_alt_count': 'int',
                   'pct_normal_alt': 'float',
                   'tumor_ref_count': 'int',
                   'tumor_alt_count': 'int',
                   'pct_tumor_alt': 'float',
                   't/n_pct_alt_ratio': 'float',
                   'gene': 'str'}


def get_media_path():
    """
    The path to /viewer/files is different in DEBUG vs Non-DEBUG
    :return:
    """
    if settings.DEBUG:
        media_path = settings.MEDIA_ROOT
    else:
        media_path = settings.MEDIA_URL
    print "settings.DEBUG is {}, set media_path to: {}".format(settings.DEBUG,
                                                               media_path)
    return media_path


def is_loaded(report):
    """
    Return true if variants for this report are loaded in the db
    :param report:
    :return:
    """
    if report.pk in list(set(
            Variant.objects.values_list('report', flat=True))):
        return True
    else:
        return False


def get_header_cols_and_delim(filehandle):
    """
    Return header content, as well as the delimiter
    :param filehandle:
    :return:
    """
    header_line = filehandle.readline().strip()
    #print "Header line: {}".format(header_line)
    splitby = ','
    if '\t' in header_line:
        splitby = '\t'
    cols = header_line.split(splitby)
    #print "Split cols: {}".format(cols)
    return {'cols': cols, 'delim': splitby }


def classify_headers(header_list):
    """
    compare headers from a file to those expected by the database.  Any column
    not accounted for will be sent back in a separate list, and stored in a
    string: effect=EXON;coding=CODING;
    :param header_list: list of column headers
    :returns list of lists: [[canonical headers], [non-canonical headers]]
    """
    canonical = []
    extra = []
    for h in header_list:
        if h in variant_headers:
            canonical.append(h)
        else:
            extra.append(h)
    return (canonical, extra)


def add_goodies(atoms, headers, md_anderson_genes, eMERGE_genelist):
    """
    Process a line of a report, add html links out, gene list tags, etc
    :param atoms: record content in a list
    :param headers: corresponding header titles
    :param md_anderson_genes: dict of gene-names: URLs
    :param eMERGE_genelist: dict of gene-names
    """
    for i in range(0, len(headers)):
        if not atoms[i]:
            atoms[i] = ''
        # highlight NON_SYNONYMOUS_CODING
        if headers[i] == 'effect' and atoms[i] == 'NON_SYNONYMOUS_CODING':
            atoms[i] = "<span style=\"color:green\">%s</span>" % atoms[i]
        # add MDAnderson and eMERGE links to appropriate gene names
        if (headers[i] == 'gene') and (atoms[i] is not None):
            # link to genecards
            gene_card = ('<a href=\"http://www.genecards.org/index.php?' +
                         'path=/Search/keyword/{g}\" target=\"_blank\" ' +
                         'title=\"GeneCards Link\">{g}</a>').format(g=atoms[i])

            # construct additional links out
            gene_str_extension = '<br/><span style=\"font-size:x-small\">'

            if atoms[i].lower() in md_anderson_genes:
                gene_str_extension += '<a href=\"{link}\" target=\"_blank\" title=\"MDAnderson Cancer Center\">MDAnderson</a>'.format(
                        link=md_anderson_genes[atoms[i].lower()])

            if atoms[i].upper() in eMERGE_genelist:
                gene_str_extension += ' eMERGE'

            # assemble additional links
            new_link = '{gene_card}{ext}</span>'.format(gene_card=gene_card,
                                                   ext=gene_str_extension)
            # apply changes
            atoms[i] = new_link

    return atoms


def get_mdanderson_genes():
    with open(settings.LINKS_OUT + 'mdanderson.json', 'r') as md_f:
        return json.loads(json.load(md_f))


def get_eMERGE_genelist():
    eMERGE_genelist = []
    with open(settings.LINKS_OUT + 'eMERGE_genelist.txt', 'r') as e_f:
        for line in e_f:
            gene = line.rstrip()
            if gene:
                eMERGE_genelist.append(gene)
    return eMERGE_genelist


def json_from_report(filename):
    print "%s - creating json from: %s" % (os.getcwd(), filename)
    report_file = open(filename, 'r')
    header_line_dict = get_header_cols_and_delim(report_file)
    cols = header_line_dict['cols']
    splitby = header_line_dict['delim']

    md_anderson_genes = get_mdanderson_genes()
    eMERGE_genelist = get_eMERGE_genelist()

    d = []
    for line in report_file:
        tokens = line.rstrip('\n').split(splitby)
        if len(tokens) > 1:
            if 'INTRON' not in line and 'INTERGENIC' not in line:
                formatted_line = add_goodies(tokens, cols, md_anderson_genes, eMERGE_genelist)
                d.append(formatted_line)
    data = tablib.Dataset(*d, headers=cols)
    return data

def json_from_ajax(db_response):
    # Make sure query returned some data
    # If not, report back empty
    if len(db_response) == 0:
        return ''

    md_anderson_genes = get_mdanderson_genes()
    eMERGE_genelist = get_eMERGE_genelist()

    # Pull headers, sort into alphabetical order
    # This is so it's in the same order returned
    # by Variant._meta.get_all_field_names()
    headers = []
    for header in db_response.values()[0]:
        headers.append(header)
    headers.sort()

    # Grab and store pre-rearranged indexes of relevant headers
    col_order = [headers.index('chrom'), headers.index('pos'), headers.index('gene_name'), headers.index('ref'),
                  headers.index('alt'), headers.index('normal_ref_count'), headers.index('normal_alt_count'),
                  headers.index('tumor_ref_count'), headers.index('tumor_alt_count')]

    # Rearrage headers
    new_headers = []
    for i in col_order:
        new_headers.append(headers[i])
        headers[i] = None
    map(lambda x: new_headers.append(x) if x else False, headers)
    headers = new_headers

    # Append extra headers to front
    headers.insert(0, 'BnIDs')
    headers.insert(0, 'sample')
    headers.insert(0, 'study')

    # Temporary to make search and view report agree on the header for the gene name
    # TODO
    headers[headers.index('gene_name')] = 'gene'

    # Parse list of variant records
    variant_records = []
    for variant in db_response:
        # Get all field names, delete report object
        field_names = Variant._meta.get_all_field_names()
        del field_names[field_names.index('report')]

        # Pull relevent fields from variant object
        record = []
        for key in field_names:
            if key in variant.__dict__:
                record.append(variant.__dict__[key])

        # Replace all None with empty string
        record = ['' if elem is None else elem for elem in record]

        # Sort the records into desired order
        new_record = []
        for i in col_order:
            new_record.append(record[i])
            record[i] = None
        map(lambda x: new_record.append(x) if x is not None else False, record)
        record = new_record

        # Append extra data to front
        bnids, samples = [], set()
        for bnid in variant.report.bnids.all():
            bnids.append(bnid.bnid)
            samples.add(bnid.sample.name)
        bnids = map(str, bnids)
        samples = map(str, samples)
        study = variant.report.study.name
        record = [study, str(samples), str(bnids)] + record

        # This doesn't allow through records that have INTRON or INTERGENIC
        # Is that what we want?
        # TODO
        if len(record) > 1:
            if 'INTRON' not in record and 'INTERGENIC' not in record:
                formatted_record = add_goodies(record, headers, md_anderson_genes, eMERGE_genelist)
                # Append this record to list of all records
                variant_records.append(formatted_record)

    # Return as an html table
    return tablib.Dataset(*variant_records, headers=headers).html


def report_file_formatter(filename):
    """
    Fix column headers, and check for missing required columns
    :param filename: string of just the name, no path
    :return checks_out: boolean, True - formatted and works, False - bad
    """
    checks_out = True
    # make a copy of the original
    media_path = get_media_path()
    shutil.copy(os.path.join(media_path, filename),
                os.path.join(media_path, 'original_files',
                             filename)
                )
    report_file = open(os.path.join(media_path, filename), 'r')
    header_line_dict = get_header_cols_and_delim(report_file)
    delimiter = header_line_dict['delim']

    # start off in all lowercase
    cols = [x.lower() for x in header_line_dict['cols']]
    cols = [x.replace('%', 'pct') for x in cols]

    # check for mandatory columns: chr, pos, ref, alt
    missing_list = []
    for c in ['chr', 'pos', 'ref', 'alt']:
        if c not in cols:
            missing_list.append(c)

    if len(missing_list) > 0:
        msg = "ERROR: Mandatory columns [{}] missing from report file " + \
              "headers\n{}"
        print msg.format(', '.join(missing_list), cols)
        checks_out = False
    else:
        # print to temp file
        temp_report_file = open(os.path.join(media_path, filename + '.tmp'),'w')

        print >>temp_report_file, delimiter.join(cols)
        for line in report_file:
            print >>temp_report_file, line.rstrip()
        shutil.move(os.path.join(media_path, filename + '.tmp'),
                    os.path.join(media_path, filename)
                    )

    return checks_out


def load_into_db(report):
    """
    If report hasn't been loaded, and fits format, bulk load into db
    :param report:
    :return boolean:
    """
    if is_loaded(report):
        return False

    media_path = get_media_path()
    print "{}/{}".format(media_path, report.report_file.name)

    checks_out = report_file_formatter(report.report_file.name)
    if checks_out:
        print "{} checks out.".format(media_path + report.report_file.name)

    report_file = open(media_path + report.report_file.name, 'r')
    header_line_dict = get_header_cols_and_delim(report_file)
    headers = header_line_dict['cols']
    (canonical, extra_headers) = classify_headers(headers)
    print "Canonical: {}\nExtra: {}".format(canonical, extra_headers)
    splitby = header_line_dict['delim']

    all_variants = []
    for line in report_file:
        #print "line: {}".format(line)
        data = line.rstrip('\n').split(splitby)
        if len(data) > 1:
            variant = Variant()

            variant.report = report
            # process canonical
            for h in canonical:
                if h in headers:
                    # process the ints
                    if variant_headers[h] == 'int':
                        if data[headers.index(h)]:
                            setattr(variant, h, int(data[headers.index(h)]))
                    # process the floats
                    elif variant_headers[h] == 'float':
                        field = h
                        if '%' in h:
                            field = h.replace('%', 'pct')
                        data[headers.index(h)] = data[headers.index(h)].replace('%', '')
                        if data[headers.index(h)]:
                            setattr(variant, field, float(data[headers.index(h)]))
                    # process the strings
                    elif variant_headers[h] == 'str':
                        field = h
                        if h == 'chr':
                            field = 'chrom'
                        if h == 'gene':
                            field = 'gene_name'
                        setattr(variant, field, data[headers.index(h)])
            # process extra fields
            extra_headers_list = []
            for eh in extra_headers:
                if data[headers.index(eh)]:
                    extra_headers_list.append(
                        '{}={}'.format(eh, data[headers.index(eh)])
                    )
            variant.extra_info = ';'.join(extra_headers_list)
            # this is too slow, 1000000% too slow. do in bulk.
            # variant.save()
            all_variants.append(variant)

    # process all at once
    Variant.objects.bulk_create(all_variants)
    print "Loaded {} variants from file: {}".format(
        len(all_variants), report_file.name
    )
    return True

