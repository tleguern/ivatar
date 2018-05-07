"use strict";

// Autofocus the right field on forms
if (document.forms.login) {
    if (document.forms.login.username) {
        document.forms.login.username.focus();
    } else if (document.forms.login.openid_identifier) {
        document.forms.login.openid_identifier.focus();
    }
} else if (document.forms.addemail) {
    document.forms.addemail.email.focus();
} else if (document.forms.addopenid) {
    document.forms.addopenid.openid.focus();
} else if (document.forms.changepassword) {
    document.forms.changepassword.old_password.focus();
} else if (document.forms.deleteaccount) {
    if (document.forms.deleteaccount.password) {
        document.forms.deleteaccount.password.focus();
    }
} else if (document.forms.lookup) {
    if (document.forms.lookup.email) {
        document.forms.lookup.email.focus();
    } else if (document.forms.lookup.domain) {
        document.forms.lookup.domain.focus();
    }
} else if (document.forms.newaccount) {
    document.forms.newaccount.username.focus();
} else if (document.forms.reset) {
    document.forms.reset.email.focus();
}
