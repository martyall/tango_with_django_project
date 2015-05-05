from django import forms
from django.contrib.auth.models import User
from rango.models import Page, Category, UserProfile


class CategoryForm(forms.ModelForm):
    name = forms.CharField(max_length=128, help_text='Please enter the category name.')
    views = forms.IntegerField(widget=forms.HiddenInput(),initial=0)
    likes = forms.IntegerField(widget=forms.HiddenInput(),initial=0)
    slug = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Category
        fields = ('name',)

class PageForm(forms.ModelForm):
    title = forms.CharField(max_length=128, help_text='Please enter the title.')
    url = forms.URLField(max_length=200, help_text='Please enter the URL.')
    views = forms.IntegerField(widget=forms.HiddenInput(), initial=0)

    def clean(self):
        cleaned_data = self.cleaned_data
        url = cleaned_data.get('url')

        # if url is empty and doesn't start with http:// then fix it
        if url and not url.startswith('http://'):
            url = 'http://' + url
            cleaned_data['url'] = url

        return cleaned_data


    class Meta:
        model = Page
        
        # What fields to include in our forms?
        # This way we don't we need every field in the model present
        # some fields may allow NULL values, so we probably don't care about those.
        # here, we are hiding the foreign key
        # we can either exclude the cateogry field from the form
        # or secify the fields to include
        # fields('title',etc)
        exclude = ('category',)

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('website','picture')
