#global prever rcX
%global _hardened_build 1

Summary: DNSSEC key and zone management software
Name: opendnssec
Version: 1.4.7
Release: 3%{?prever}%{?dist}
License: BSD
Url: http://www.opendnssec.org/
Source0: http://www.opendnssec.org/files/source/%{?prever:testing/}%{name}-%{version}%{?prever}.tar.gz
Source1: ods-enforcerd.service
Source2: ods-signerd.service
Source3: ods.sysconfig
Source4: conf.xml
Source5: tmpfiles-opendnssec.conf
Source6: opendnssec.cron

Patch0: opendnssec-1.4.7-1204100-extract.patch
Patch1: 0001-use-system-trang.patch
Patch2: 0002-get-started.patch

Group: Applications/System
Requires: opencryptoki, softhsm >= 2.0.0b1-2, systemd-units
BuildRequires: libxml2, libxslt
Requires: libxml2, libxslt
BuildRequires: ldns-devel >= 1.6.12, sqlite-devel , openssl-devel
BuildRequires: libxml2-devel, doxygen, trang
# It tests for pkill/killall and would use /bin/false if not found
BuildRequires: procps-ng
BuildRequires: systemd-units
BuildRequires: sed
Requires(pre): shadow-utils
Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units
%if 0%{?prever:1}
#For building snapshots
Buildrequires: autoconf, automake, libtool, java
%endif

%description
OpenDNSSEC was created as an open-source turn-key solution for DNSSEC.
It secures zone data just before it is published in an authoritative
name server. It requires a PKCS#11 crypto module library, such as softhsm.

This is UNSUPPORTED EXPERIMENTAL package.

%prep
%setup -q -n %{name}-%{version}%{?prever}
# bump default policy ZSK keysize to 2048
sed -i "s/1024/2048/" conf/kasp.xml.in
%patch0 -p1 -b .p0.allow_extraction
%patch1 -p1 -b .p0.system_trang
%patch2 -p1
# fix platform-specific paths in conf.xml
sed -i 's:<Module>/usr/lib64:<Module>%{_libdir}:' %{SOURCE4}

%build
export LDFLAGS="-Wl,-z,relro,-z,now -pie -specs=/usr/lib/rpm/redhat/redhat-hardened-ld"
export CFLAGS="$RPM_OPT_FLAGS -fPIE -pie -Wextra -Wformat -Wformat-nonliteral -Wformat-security"
export CXXFLAGS="$RPM_OPT_FLAGS -fPIE -pie -Wformat-nonliteral -Wformat-security"
%configure --with-ldns=%{_libdir} --without-cunit
make %{?_smp_mflags}

%check
# Requires sample db not shipped with upstream
# It also requires CUnit-devel package which is not in RHEL
# make check

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install
mkdir -p %{buildroot}/var/opendnssec/{tmp,signed,signconf}
install -d -m 0755 %{buildroot}%{_initrddir} %{buildroot}%{_sysconfdir}/cron.d/
install -m 0644 %{SOURCE6} %{buildroot}/%{_sysconfdir}/cron.d/opendnssec
rm -f %{buildroot}/%{_sysconfdir}/opendnssec/*.sample
install -d -m 0755 %{buildroot}/%{_sysconfdir}/sysconfig 
install -d -m 0755 %{buildroot}%{_unitdir}
install -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/
install -m 0644 %{SOURCE2} %{buildroot}%{_unitdir}/
install -m 0644 %{SOURCE3} %{buildroot}/%{_sysconfdir}/sysconfig/ods
install -m 0644 %{SOURCE4} %{buildroot}/%{_sysconfdir}/opendnssec/
mkdir -p %{buildroot}%{_sysconfdir}/tmpfiles.d/
install -m 0644 %{SOURCE5} %{buildroot}%{_sysconfdir}/tmpfiles.d/opendnssec.conf
mkdir -p %{buildroot}%{_localstatedir}/run/opendnssec

%files 
%{_unitdir}/ods-enforcerd.service
%{_unitdir}/ods-signerd.service
%config(noreplace) %{_sysconfdir}/tmpfiles.d/opendnssec.conf
%attr(0770,root,ods) %dir %{_sysconfdir}/opendnssec
%attr(0775,root,ods) %dir %{_localstatedir}/opendnssec
%attr(0770,root,ods) %dir %{_localstatedir}/opendnssec/tmp
%attr(0775,root,ods) %dir %{_localstatedir}/opendnssec/signed
%attr(0770,root,ods) %dir %{_localstatedir}/opendnssec/signconf
%attr(0660,root,ods) %config(noreplace) %{_sysconfdir}/opendnssec/*.xml
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/sysconfig/ods
%attr(0770,root,ods) %dir %{_localstatedir}/run/opendnssec
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/cron.d/opendnssec
%doc NEWS README.md LICENSE GETSTARTED
%{_mandir}/*/*
%{_sbindir}/*
%{_bindir}/*
%attr(0770,root,ods) %dir %{_datadir}/%{name}
%{_datadir}/%{name}/*

%pre
getent group ods >/dev/null || groupadd -r ods
getent passwd ods >/dev/null || \
useradd -r -g ods -d /etc/opendnssec -s /sbin/nologin \
-c "opendnssec daemon account" ods
exit 0

%post
# in case we update any xml conf file
ods-ksmutil update all >/dev/null 2>/dev/null ||:
%systemd_post ods-enforcerd.service
%systemd_post ods-signerd.service


%preun
%systemd_preun ods-enforcerd.service
%systemd_preun ods-signerd.service

%postun
%systemd_postun_with_restart ods-enforcerd.service
%systemd_postun_with_restart ods-signerd.service

%changelog
* Thu Sep 10 2015 Paul Wouters <pwouters@redhat.com> - 1.4.7-3
- Resolves: rhbz#1261530 /etc/opendnssec is not writeable by ods user

* Thu Jun 11 2015 Paul Wouters <pwouters@redhat.com> - 1.4.7-2
- Resolves: rhbz#1230287 ods-signerd.service Unknown lvalue 'After'

* Tue Mar 31 2015 Paul Wouters <pwouters@redhat.com> - 1.4.7-1
- Resolves: rhbz#1204100 Rebase to opendnssec 1.4.7+

* Tue Sep 30 2014 Petr Spacek <pspacek@redhat.com> - 1.4.6-3
- Updated spec to build platform-indepent conf.xml

* Tue Sep 30 2014 Paul Wouters <pwouters@redhat.com> - 1.4.6-2
- Changed conf.xml to reference softhsm at /usr/lib64/pkcs11/libsofthsm2.so
- Updated Requires: to softhsm >= 2.0.0b1-2

* Mon Sep 22 2014 Petr Spacek <pspacek redhat com> - 1.4.6-1
- Imported version 1.4.6
- Added patch which adds configuration option <AllowExtraction/>

