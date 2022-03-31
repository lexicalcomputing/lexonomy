%global debug_package %{nil}
%global __python %{__python3}
%define __requires_exclude coffee

Name:		lexonomy
Version:	0
Release:	1%{?dist}
Summary:	Lexonomy, a cloud-based, open-source platform for writing and publishing dictionaries.

Group:		Applications/Text
License:	Copyright (c) 2017-2022 Michal Boleslav Měchura, Lexical Computing CZ s.r.o.
URL:		https://www.lexonomy.eu/
Source0:	lexonomy-%{version}.tar.gz

BuildRequires:	python3 >= 3.5
BuildRequires:	git
BuildRequires:	nodejs
BuildRequires:	npm

Requires:	python3 >= 3.5
Requires:	python3-jwt
Requires:	python3-markdown
Requires:	python3-paste
Requires:	python3-pyicu
Requires:	python3-requests


%description
Lexonomy is a free tool for writing and publishing dictionaries and other dictionary-like things. Lexonomy runs in your web browser and all data is stored on the server, so you don't have to install anything on your computer. This page will give you a brief introduction to Lexonomy, showing you how to create a simple dictionary and how to publish it on the web.

%prep
%setup -n lexonomy-%{version}


%build
cd website
make

%install
DESTDIR=$RPM_BUILD_ROOT INSTALLDIR=/opt/lexonomy/ make install
echo %{version} > $RPM_BUILD_ROOT/opt/lexonomy/website/version.txt

%post
chown -R apache: /opt/lexonomy/data
chmod -R g+rwX /opt/lexonomy/data


%files
/opt/lexonomy/
%config(noreplace) /opt/lexonomy/data
%config(noreplace) /opt/lexonomy/website/siteconfig.json

%changelog
