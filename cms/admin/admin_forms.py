from django import forms
from django.forms.models import ModelForm, modelformset_factory
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.forms import BaseGenericInlineFormSet

from ..forms import ReadonlyInput
from ..models import Block, Image
from .. import settings as cms_settings


class BaseContentFormSet(BaseGenericInlineFormSet):
    '''Just like BaseGenericInlineFormSet, except it doesn't rely on ct_field 
       being an actual ForeignKey (it can be an integer field containing
       the ctype id, but not linked at the database level.)'''
    
    def __init__(self, data=None, files=None, instance=None, save_as_new=None,
                 prefix=None, queryset=None, **kwargs):
        opts = self.model._meta
        self.instance = instance
        self.rel_name = '-'.join((
            opts.app_label, opts.model_name,
            self.ct_field.name, self.ct_fk_field.name,
        ))
        if self.instance is None or self.instance.pk is None:
            qs = self.model._default_manager.none()
        else:
            if queryset is None:
                queryset = self.model._default_manager
            ctype = ContentType.objects.get_for_model(self.instance, 
                                                      for_concrete_model=True)
            qs = queryset.filter(
                content_type_id=ctype.id,
                object_id=self.instance.pk,
            )
        super(BaseGenericInlineFormSet, self).__init__(
            queryset=qs, data=data, files=files,
            prefix=prefix,
            **kwargs
        )


def content_inlineformset_factory(model, form=ModelForm,
                                  formset=BaseContentFormSet,
                                  ct_field="content_type_id",
                                  fk_field="object_id",
                                  fields=None, exclude=None,
                                  extra=3, can_order=False, can_delete=True,
                                  max_num=None, formfield_callback=None,
                                  validate_max=False, for_concrete_model=True,
                                  min_num=None, validate_min=False):
    '''Returns a BaseContentFormSet for the given kwargs. Basically 
       identical to generic_inlineformset_factory but uses BaseContentFormSet
       instead of BaseGenericInlineFormSet.'''

    opts = model._meta
    # if there is no field called `ct_field` let the exception propagate
    ct_field = opts.get_field(ct_field)
    fk_field = opts.get_field(fk_field)  # let the exception propagate
    if exclude is not None:
        exclude = list(exclude)
        exclude.extend([ct_field.name, fk_field.name])
    else:
        exclude = [ct_field.name, fk_field.name]
    FormSet = modelformset_factory(model, form=form,
                                   formfield_callback=formfield_callback,
                                   formset=formset,
                                   extra=extra, can_delete=can_delete, can_order=can_order,
                                   fields=fields, exclude=exclude, max_num=max_num,
                                   validate_max=validate_max, min_num=min_num,
                                   validate_min=validate_min)
    FormSet.ct_field = ct_field
    FormSet.ct_fk_field = fk_field
    FormSet.for_concrete_model = for_concrete_model
    return FormSet


class InlineBlockForm(forms.ModelForm):
    class Meta:
        model = Block
        fields = ('content', )

    def __init__(self, *args, **kwargs):
        super(InlineBlockForm, self).__init__(*args, **kwargs)

        # change the content widget based on the format of the block - a bit hacky but best we can do
        if 'instance' in kwargs:
            format = kwargs['instance'].format
            if format == Block.FORMAT_ATTR:
                self.fields['content'].widget = forms.TextInput()                
            self.fields['content'].widget.attrs['class'] = " cms cms-%s" % format

        required_cb = cms_settings.BLOCK_REQUIRED_CALLBACK
        if callable(required_cb) and 'instance' in kwargs:
            self.fields['content'].required = required_cb(kwargs['instance'])


class InlineImageForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ('file', 'description', )

    def __init__(self, *args, **kwargs):
        super(InlineImageForm, self).__init__(*args, **kwargs)

        required_cb = cms_settings.IMAGE_REQUIRED_CALLBACK
        if callable(required_cb) and 'instance' in kwargs:
            self.fields['file'].required = required_cb(kwargs['instance'])


class BlockForm(InlineBlockForm):
    label = forms.CharField(widget=ReadonlyInput)
    
    class Meta:
        model = Block
        fields = ('label', 'content', )


class ImageForm(InlineImageForm):
    label = forms.CharField(widget=ReadonlyInput)
    
    class Meta:
        model = Image
        fields = ('label', 'file', 'description', )