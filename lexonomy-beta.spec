%global debug_package %{nil}
%global __python %{__python3}
%define __requires_exclude coffee
%define _build_id_links none

Name: lexonomy-beta
Version:	0
Release:	1%{?dist}
Summary:	Lexonomy, a cloud-based, open-source platform for writing and publishing dictionaries.

Group:		Applications/Text
License:	Copyright (c) 2017-2022 Michal Boleslav Měchura, Lexical Computing CZ s.r.o.
URL:		https://www.lexonomy.eu/
Source0: lexonomy-beta-%{version}.tar.gz

BuildRequires:	make
BuildRequires:	python3 >= 3.8
BuildRequires:	git
BuildRequires:	nodejs
BuildRequires:	npm

Requires:	python3 >= 3.8
Requires:	python3-jwt
Requires:	python3-markdown
Requires:	python3-paste
Requires:	python3-pyicu
Requires:	python3-requests
Requires:	python3-bottle
Requires:	python3-unidecode
Requires:	sqlite >= 3.40


%description
Lexonomy is a free tool for writing and publishing dictionaries and other dictionary-like things. Lexonomy runs in your web browser and all data is stored on the server, so you don't have to install anything on your computer. This page will give you a brief introduction to Lexonomy, showing you how to create a simple dictionary and how to publish it on the web.

%prep
%setup -n lexonomy-beta-%{version}

%build
make

%install
make DESTDIR=$RPM_BUILD_ROOT INSTALLDIR=/usr/share/lexonomy-beta/ install
echo %{version} > $RPM_BUILD_ROOT/usr/share/lexonomy-beta/website/version.txt
sed -i -e 's/@VERSION@/%{version}/g' $RPM_BUILD_ROOT/usr/share/lexonomy-beta/website/index*html

%post
make -C /usr/share/lexonomy-beta/ deploy DEPLOYDIR=/opt/lexonomy-beta/
chgrp -R `id -g apache` /opt/lexonomy-beta/data

%files
/usr/share/lexonomy-beta/

%changelog
