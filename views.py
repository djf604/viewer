from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.core.context_processors import csrf
from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.template import RequestContext
import simplejson

#from django_ajax.decorators import ajax

from forms import BnidForm, SampleForm, ReportForm, StudyForm, UserForm
from forms import StudySelectorForm
from models import Bnid, Sample, Report, Study, Variant
from access_tests import in_proj_user_group

from util import report_parser

import tablib


def index(request):
    return render(request, 'viewer/index.html', {})


def register(request):
    registered = False
    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        if user_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()
            registered = True
            firstname = user_form['first_name'].value()
            lastname = user_form['last_name'].value()
            subject = 'Report Viewer Registration: {}, {}'.format(
                lastname, firstname)
            message = 'User {} {} <{}> has registered and needs to be vetted.'.format(
                firstname, lastname, user.email)
            send_mail(subject, message, 'jgrundstad@uchicago.edu',
                      ['jgrundstad@uchicago.edu'], fail_silently=False)
        else:
            print user_form.errors
    else:
        user_form = UserForm()
    context = {'user_form': user_form, 'registered': registered}
    context.update(csrf(request))
    return render_to_response('viewer/register.html', context,
                              context_instance=RequestContext(request))


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect('/viewer/')
            else:
                # user is inactive
                return HttpResponse("Sorry, your account is disabled.")
        else:
            # Bad login details
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login details provided.")
    else:
        context = {}
        context.update(csrf(request))
        return render(request, 'viewer/login.html', context)


def restricted(request):
    context = {}
    return render(request, '/viewer/index.html', context)


def permission(request):
    context = {}
    return render(request, '/viewer/permission.html', context)


@user_passes_test(in_proj_user_group)
def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/viewer/')

'''
Study model
'''
@user_passes_test(in_proj_user_group)
def manage_study(request):
    context = {'studies': Study.objects.all()}
    context.update(csrf(request))
    return render_to_response('viewer/study/manage_study.html', context,
                              context_instance=RequestContext(request))

@user_passes_test(in_proj_user_group)
def new_study(request):
    if request.method == 'POST':
        sform = StudyForm(request.POST, instance=Study())
        if sform.is_valid():
            sform.save()
        return HttpResponseRedirect('/viewer/study/')
    else:
        sform = StudyForm(instance=Study())
        context = {'study_form': sform}
        context.update(csrf(request))
        return render_to_response('viewer/study/new_study.html', context,
                                  context_instance=RequestContext(request))

@user_passes_test(in_proj_user_group)
def edit_study(request, study_id):
    if request.method == 'POST':
        s = Study.objects.get(pk=study_id)
        updated_form = StudyForm(request.POST, instance=s)
        if updated_form.is_valid():
            updated_form.save()
            return HttpResponseRedirect('/viewer/study/')
    else:
        study_obj = Study.objects.get(pk=study_id)
        sform = StudyForm(instance=study_obj)
        context = {'study_form': sform, 'name': study_obj.name, 'pk': study_obj.pk}
        context.update(csrf(request))
        return render_to_response('viewer/study/edit_study.html', context,
                                  context_instance=RequestContext(request))

@user_passes_test(in_proj_user_group)
def delete_study(request, study_id):
    if request.method == 'POST':
        Study.objects.get(pk=study_id).delete()
        return HttpResponseRedirect('/viewer/study/')
    else:
        study_obj = Study.objects.get(pk=study_id)
        context = {'name': study_obj.name, 'pk': study_obj.pk}
        context.update(csrf(request))
        return render_to_response('viewer/study/delete_study.html', context,
                                  context_instance=RequestContext(request))

'''
Sample model
'''
@user_passes_test(in_proj_user_group)
def manage_sample(request):
    context = {'samples': Sample.objects.all()}
    context.update(csrf(request))
    return render(request, 'viewer/sample/manage_sample.html', context)

@user_passes_test(in_proj_user_group)
def new_sample(request):
    if request.method == 'POST':
        sform = SampleForm(request.POST, instance=Sample())
        if sform.is_valid():
            sform.save()
        return HttpResponseRedirect('/viewer/sample/')
    else:
        sform = SampleForm(instance=Sample())
        context = {'sample_form': sform}
        context.update(csrf(request))
        return render_to_response('viewer/sample/new_sample.html', context,
                                  context_instance=RequestContext(request))

@user_passes_test(in_proj_user_group)
def edit_sample(request, sample_id):
    if request.method == 'POST':
        s = Sample.objects.get(pk=sample_id)
        updated_form = SampleForm(request.POST, instance=s)
        if updated_form.is_valid():
            updated_form.save()
            return HttpResponseRedirect('/viewer/sample/')
    else:
        sample_obj = Sample.objects.get(pk=sample_id)
        sform = SampleForm(instance=sample_obj)
        context = {'sample_form': sform, 'name': sample_obj.name, 'pk': sample_obj.pk}
        context.update(csrf(request))
        return render_to_response('viewer/sample/edit_sample.html', context,
                                  context_instance=RequestContext(request))

@user_passes_test(in_proj_user_group)
def delete_sample(request, sample_id):
    if request.method == 'POST':
        Sample.objects.get(pk=sample_id).delete()
        return HttpResponseRedirect('/viewer/sample')
    else:
        sample_obj = Sample.objects.get(pk=sample_id)
        context = {'name': sample_obj.name, 'pk': sample_obj.pk}
        context.update(csrf(request))
        return render(request, 'viewer/sample/delete_sample.html', context)

'''
Bionimbus ID model
'''
@user_passes_test(in_proj_user_group)
def manage_bnid(request):
    context = {'bnids': Bnid.objects.all()}
    context.update(csrf(request))
    return render(request, 'viewer/bnid/manage_bnid.html', context)

@user_passes_test(in_proj_user_group)
def new_bnid(request): #study_id=None, **kwargs):
    #if study_id:
        #print "Got study_id: {}".format(study_id)
    if request.method == 'POST':
        bform = BnidForm(request.POST, instance=Bnid())
        print bform['sample']
        print bform['bnid']
        if bform.is_valid():
            bform.save()
        return HttpResponseRedirect('/viewer/bnid/')
    else:
        bform = BnidForm(instance=Bnid())
        ss_form = StudySelectorForm()
        context = {'bnid_form': bform, 'study_selector_form': ss_form}
        context.update(csrf(request))
        return render_to_response('viewer/bnid/new_bnid.html', context,
                                  context_instance=RequestContext(request))

@user_passes_test(in_proj_user_group)
def edit_bnid(request, bnid_id):
    if request.method == 'POST':
        b = Sample.objects.get(pk=bnid_id)
        updated_form = BnidForm(request.POST, instance=b)
        if updated_form.is_valid():
            updated_form.save()
            return HttpResponseRedirect('/viewer/bnid/')
    else:
        bnid_obj = Bnid.objects.get(pk=bnid_id)
        bform = BnidForm(instance=bnid_obj)
        ss_form = StudySelectorForm()
        context = {'bnid_form': bform,
                   'bnid': bnid_obj.bnid,
                   'pk': bnid_obj.pk,
                   'study_selector_form': ss_form}
        context.update(csrf(request))
        return render_to_response('viewer/bnid/edit_bnid.html', context,
                                  context_instance=RequestContext(request))

@user_passes_test(in_proj_user_group)
def delete_bnid(request, bnid_id):
    if request.method == 'POST':
        Bnid.objects.get(pk=bnid_id).delete()
        return HttpResponseRedirect('/viewer/bnid/')
    else:
        bnid_obj = Bnid.objects.get(pk=bnid_id)
        context = {'bnid': bnid_obj.bnid, 'pk': bnid_obj.pk}
        context.update(csrf(request))
        return render(request, 'viewer/bnid/delete_bnid.html', context)

'''
Report model
'''
@user_passes_test(in_proj_user_group)
def manage_report(request):
    context = {'reports': Report.objects.all()}
    context.update(csrf(request))
    return render(request, 'viewer/report/manage_report.html', context)

@user_passes_test(in_proj_user_group)
def upload_report(request):
    if request.method == 'POST':
        print "POST from upload_report"
        if request.FILES:
            rform = ReportForm(request.POST, request.FILES)
        else:
            rform = ReportForm(request.POST)
        if rform.is_valid():
            rform.save()
            return HttpResponseRedirect('/viewer/report/')
        else:
            print "rform (ReportForm) is Invalid"
            print str(rform)
    else:
        rform = ReportForm(instance=Report(), initial={})
        context = {'report_form': rform}
        context.update(csrf(request))
        return render_to_response('viewer/report/upload_report.html', context,
                                  context_instance=RequestContext(request))

@user_passes_test(in_proj_user_group)
def edit_report(request, report_id):
    if request.method == 'POST':
        r = Report.objects.get(pk=report_id)
        updated_form = ReportForm(request.POST, instance=r)
        if updated_form.is_valid():
            updated_form.save()
            return HttpResponseRedirect('/viewer/report')
    else:
        report_obj = Report.objects.get(pk=report_id)
        rform = ReportForm(instance=report_obj)
        context = {'report_form': rform,
                   'report': report_obj.report_file,
                   'pk': report_id,}
        context.update(csrf(request))
        return render_to_response('viewer/report/edit_report.html', context,
                                  context_instance=RequestContext(request))

@user_passes_test(in_proj_user_group)
def view_report(request, file_id):
    # build context from file
    print 'file_id: %s' % file_id
    report_obj = Report.objects.get(pk=file_id)
    report_data = report_parser.json_from_report(settings.MEDIA_ROOT + \
                                                 report_obj.report_file.name)

    #print report_data
    report_html = str(report_data.html)
    # add table class and id
    report_html = report_html.replace("<table>",
        "<table class=\"table table-hover\" id=\"report-table\">")

    #print report_html
    context = {'report_html': report_html,
               'filename': report_obj.report_file.name.split('/')[1],
               'study': report_obj.bnids.first().sample.study,
               'report_obj': report_obj}
    return render_to_response('viewer/report/view_report.html', context,
                              context_instance=RequestContext(request))

def delete_report(request, report_id):
    if request.method == 'POST':
        Report.objects.get(pk=report_id).delete()
        return HttpResponseRedirect('/viewer/report/')
    else:
        report_obj = Report.objects.get(pk=report_id)
        context = {'name': report_obj.report_file.name.strip('./'), 'pk': report_obj.pk}
        return render(request, 'viewer/report/delete_report.html', context)

'''
Search functions
'''
@user_passes_test(in_proj_user_group)
def search_reports(request):
    variant_fields = Variant._meta.get_all_field_names()
    context = {'variant_fields':variant_fields}
    return render(request, 'viewer/search/search_reports.html', context)


@user_passes_test(in_proj_user_group)
#@ajax
def ajax_search_reports(request, search_col, search_term, search_type):
    db_lookup = '%s__%s' % (search_col, search_type)
    variants = Variant.objects.filter(**{db_lookup: search_term})
    #print variants[0].report.study.description
    # from django.core import serializers
    # vars = serializers.serialize('json', variants)
    return HttpResponse(report_parser.json_from_ajax(variants))
    #return report_parser.json_from_ajax(variants)


'''
Util functions
'''
@user_passes_test(in_proj_user_group)
def get_samples(request, study_id=None, **kwargs):
    sample_dict = {}
    if study_id:
        study = Study.objects.get(pk=study_id)
        samples = Sample.objects.filter(study=study)
        for sample in samples:
            sample_dict[sample.id] = sample.name
    return HttpResponse(simplejson.dumps(sample_dict),
                        content_type="application/json")


@user_passes_test(in_proj_user_group)
def get_bnids_by_study(request, study_id=None):
    print "study_id: {}".format(study_id)
    bnid_dict = dict()
    if study_id:
        study = Study.objects.get(pk=study_id)
        samples = Sample.objects.filter(study=study)
        for sample in samples:
            bnids = Bnid.objects.filter(sample=sample)
            for bnid in bnids:
                bnid_dict[bnid.id] = "{}".format(bnid)
    return HttpResponse(simplejson.dumps(bnid_dict),
                        content_type="application/json")

@user_passes_test(in_proj_user_group)
def load_variants(request, report_id=None):
    print "Load Variants for Report ID: {}".format(report_id)
    report_obj = Report.objects.get(pk=report_id)
    report_parser.load_into_db(report_obj)
    return HttpResponseRedirect('/viewer/report/')



