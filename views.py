from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.core.context_processors import csrf
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.template import RequestContext

from forms import BnidForm, SampleForm, ReportForm, StudyForm, UserForm
from models import Bnid, Sample, Report, Study
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
        else:
            print user_form.errors
    else:
        user_form = UserForm()
    return render(request, 'viewer/register.html', {'user_form': user_form,
                                                    'registered': registered})


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


@user_passes_test(in_proj_user_group)
def new_study(request):
    if request.method == 'POST':
        sform = StudyForm(request.POST, instance=Study())
        if sform.is_valid():
            sform.save()
        return HttpResponseRedirect('/viewer/new_study/')
    else:
        sform = StudyForm(instance=Study())
        context = {'study_form': sform}
        studies = Study.objects.all()
        context['studies'] = studies
        context.update(csrf(request))
        return render_to_response('viewer/new_study.html', context,
                                  context_instance=RequestContext(request))

@user_passes_test(in_proj_user_group)
def edit_study(request, study_id):
    if request.method == 'POST':
        s = Study.objects.get(pk=study_id)
        updated_form = StudyForm(request.POST, instance=s)
        if updated_form.is_valid():
            updated_form.save()
            return HttpResponseRedirect('/viewer/new_study/')
    else:
        study_obj = Study.objects.get(pk=study_id)
        sform = StudyForm(instance=study_obj)
        context = {'study_form': sform, 'name': study_obj.name, 'pk': study_obj.pk}
        context.update(csrf(request))
        return render_to_response('viewer/study_edit.html', context,
                                  context_instance=RequestContext(request))

@user_passes_test(in_proj_user_group)
def new_bionimbus_id(request):
    if request.method == 'POST':
        bform = BnidForm(request.POST, instance=Bnid())
        if bform.is_valid():
            bform.save()
        return HttpResponseRedirect('/viewer/new_bionimbus_id/')
    else:
        bform = BnidForm(instance=Bnid())
        context = {'bnid_form': bform}
        bnids = Bnid.objects.all().order_by('-bnid')
        context['bnids'] = bnids
        context.update(csrf(request))
        return render_to_response('viewer/new_bionimbus_id.html', context,
                                  context_instance=RequestContext(request))

@user_passes_test(in_proj_user_group)
def edit_bionimbus_id(request, bnid_id):
    if request.method == 'POST':
        b = Sample.objects.get(pk=bnid_id)
        updated_form = BnidForm(request.POST, instance=b)
        if updated_form.is_valid():
            updated_form.save()
            return HttpResponseRedirect('/viewer/new_bionimbus_id/')
    else:
        bnid_obj = Bnid.objects.get(pk=bnid_id)
        bform = BnidForm(instance=bnid_obj)
        context = {'bnid_form': bform, 'bnid': bnid_obj.bnid, 'pk': bnid_obj.pk}
        context.update(csrf(request))
        return render_to_response('viewer/bnid_edit.html', context,
                                  context_instance=RequestContext(request))

@user_passes_test(in_proj_user_group)
def new_sample(request):
    if request.method == 'POST':
        sform = SampleForm(request.POST, instance=Sample())
        if sform.is_valid():
            sform.save()
        return HttpResponseRedirect('/viewer/new_sample/')
    else:
        sform = SampleForm(instance=Sample())
        context = {'sample_form': sform}
        samples = Sample.objects.all()
        context['samples'] = samples
        context.update(csrf(request))
        return render_to_response('viewer/new_sample.html', context,
                                  context_instance=RequestContext(request))

@user_passes_test(in_proj_user_group)
def edit_sample(request, sample_id):
    if request.method == 'POST':
        s = Sample.objects.get(pk=sample_id)
        updated_form = SampleForm(request.POST, instance=s)
        if updated_form.is_valid():
            updated_form.save()
            return HttpResponseRedirect('/viewer/new_sample/')
    else:
        sample_obj = Sample.objects.get(pk=sample_id)
        sform = SampleForm(instance=sample_obj)
        context = {'sample_form': sform, 'name': sample_obj.name, 'pk': sample_obj.pk}
        context.update(csrf(request))
        return render_to_response('viewer/sample_edit.html', context,
                                  context_instance=RequestContext(request))

@user_passes_test(in_proj_user_group)
def upload_report(request):
    if request.method == 'POST':
        print "POST from upload_report"
        #print str(request)
        if request.FILES:
            rform = ReportForm(request.POST, request.FILES)
        else:
            rform = ReportForm(request.POST)
        if rform.is_valid():
            rform.save()
            return HttpResponseRedirect('/viewer/upload_report/')
        else:
            print "rform is Invalid"
            print str(rform)
    else:
        rform = ReportForm(instance=Report())
        context = {'report_form': rform}
        reports = Report.objects.all()
        context['reports'] = reports
        context.update(csrf(request))
        return render_to_response('viewer/upload_report.html', context,
                                  context_instance=RequestContext(request))


@user_passes_test(in_proj_user_group)
def view_report(request, file_id):
    # build context from file
    print 'file_id: %s' % file_id
    report_obj = Report.objects.get(pk=file_id)
    report_data = report_parser.json_from_report(settings.MEDIA_ROOT + \
                                                 report_obj.report_file.name)
    report_html = str(report_data.html)
    # add table class and id
    report_html = report_html.replace("<table>",
        "<table class=\"table table-hover tablesorter\" id=\"report-table\">")
        #"<table class=\"tablesorter\" id=\"report-table\">")
    #report_html = report_html.replace("<thead>",
    #                                  "<thead class=\"persist-header\">")


    #print report_html
    context = {'report_html': report_html,
               'filename': report_obj.report_file.name.split('/')[1],
               'study': report_obj.bnids.first().sample.study,
               'report_obj': report_obj}
    return render_to_response('viewer/view_report.html', context,
                              context_instance=RequestContext(request))
