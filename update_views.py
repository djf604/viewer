from django.shortcuts import render_to_response
from django.views.generic import UpdateView
from models import Study, Sample, Bnid, Report
from forms import StudyForm, SampleForm, BnidForm, ReportForm
__author__ = 'jgrundst'

class StudyUpdateView(UpdateView):
    model = Study
    form_class = StudyForm
    template_name = 'viewer/study/study_edit.html'

    def dispatch(self, *args, **kwargs):
        self.study_id = kwargs['pk']
        return super(StudyUpdateView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.save()
        return render_to_response('viewer/study/new_study.html', context,
                                  context_instance=RequestContext(request))
